import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from datetime import datetime
from threading import Thread
from rosslt import Tracked

# ROS dependencies
# noinspection PyBroadException
try:
    import rclpy
    from rclpy.node import Node
    from ros2topic.api import get_msg_class
    from rosslt import TrackingNode
except Exception as e:
    print(repr(e))

    # debugging stub
    class TrackingNode:
        def __init__(self, *args, **kwargs):
            pass


class MonitorNode(TrackingNode):

    def __init__(self):
        super().__init__("rosslt_monitor")
        self.sub = None
        self.msg_type = None
        self.value = None
        self.callbacks = []

    def listen_stop(self):

        # destroy old subscription
        if self.sub:
            self.destroy_subscription(self.sub)
            self.sub = None

    def listen_status(self):
        return self.sub is not None

    def listen(self, topic):

        # clear subscription
        self.listen_stop()

        # get message type
        self.msg_type = get_msg_class(self, topic, include_hidden_topics=True)
        if not self.msg_type:
            return False

        # create new subscription
        self.sub = self.create_subscription(self.msg_type, topic, self.sub_callback, 10)
        return True

    def sub_callback(self, msg):
        self.value = msg
        for cb in self.callbacks:
            cb(msg)


class TextField(ttk.Frame):

    def __init__(self, parent, read_only=False, **kwargs):

        # frame
        ttk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.read_only = read_only

        # scroll bar
        self.scroll = ttk.Scrollbar(self)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_h = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.scroll_h.pack(side=tk.BOTTOM, fill=tk.X)

        # text field
        self.contents = tk.Text(self, height=1, width=1, wrap=tk.NONE)
        self.contents.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # configure
        self.scroll.config(command=self.contents.yview)
        self.scroll_h.config(command=self.contents.xview)
        self.contents.config(yscrollcommand=self.scroll.set)
        self.contents.config(xscrollcommand=self.scroll_h.set)

        # read only
        if self.read_only:
            self.contents.config(state=tk.DISABLED)

    def append(self, text, clear=False):

        # read only
        if self.read_only:
            self.contents.config(state=tk.NORMAL)

        # append
        auto_scroll = self.scroll.get()[1] >= 0.99
        if clear:
            self.contents.delete("1.0", tk.END)
        self.contents.insert(tk.END, text)
        self.contents.update_idletasks()
        if auto_scroll:
            self.contents.yview_moveto(1)

        # read only
        if self.read_only:
            self.contents.config(state=tk.DISABLED)


class LogTab(ttk.Frame):

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # log content
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.txt_entry = TextField(self, read_only=True)
        self.txt_entry.grid(row=0, column=0, sticky=tk.NSEW)

        # subscribe to callback
        self.app = app
        if self.app.node:
            self.app.node.callbacks.append(self.callback)

    def callback(self, msg):
        self.after(0, self.append, msg)

    def append(self, msg):

        # process queue
        prefix = datetime.now().strftime("[%H:%M:%S:%f] ")
        if hasattr(msg, "data"):
            data = Tracked.from_msg(msg)
            if hasattr(data, "data"):
                self.txt_entry.append(f"{prefix}{data} - Expression({data.data.get_expression()})\n")
            else:
                self.txt_entry.append(f"{prefix}{repr(data)}\n")
        else:
            self.txt_entry.append(f"{prefix}{msg}\n")
        self.update()


class StateTab(ttk.Frame):

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # state content
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, columns=("value", "type", "expr"))
        self.tree.heading("#0", text="Node")
        self.tree.heading("#1", text="Value")
        self.tree.heading("#2", text="Type")
        self.tree.heading("#3", text="Expression")
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.map = {}
        self.msg_type = None
        self.tracked = None
        self.root = None

        # subscribe to callback
        self.app = app
        if self.app.node:
            self.app.node.callbacks.append(self.callback)
        else:
            # debug
            try:
                from visualization_msgs.msg import Marker
                from rosslt_py_msgs.msg import TrackedMarker
                self.state_update(Tracked(Marker()).to_msg(TrackedMarker))
            except ImportError:
                pass

    def callback(self, msg):
        self.after(0, self.state_update, msg)

    def value_force(self, value):

        # check if tracked
        if self.tracked is None or not self.app.node:
            messagebox.showerror(message="Message is not tracked.")
            return

        # convert to float
        try:
            value = float(value)
        except ValueError:
            messagebox.showerror(message="Invalid value.")
            return

        # get node in focus
        focus_item = self.tree.focus()
        if focus_item in self.map:
            node = self.map[focus_item]
            if isinstance(node, Tracked):
                if node.get_location().id >= 0:
                    self.app.node.force_value(node, value)
                else:
                    messagebox.showerror(message="Attribute has no source location.")
            else:
                messagebox.showerror(message="Attribute is not tracked.")
        else:
            messagebox.showerror(message="Attribute is not a value.")

    def state_update(self, msg):

        # clear tree on type change
        if self.msg_type is not type(msg):
            self.msg_type = type(msg)
            self.tree.delete(*self.tree.get_children())
            self.map.clear()
            self.root = None

        # check for tracked message
        if hasattr(msg, "loc") and msg.get_fields_and_field_types()["loc"] == "rosslt_py_msgs/LocationHeader":

            # get tracked instance
            self.tracked = Tracked.from_msg(msg)
            root = self.tracked
        else:

            # pass message as tree root
            root = msg
            self.tracked = None

        # rebuild tree
        self.root = self.tree_append(root, "root", "", self.root)
        self.update()

    def tree_append(self, node, name, parent="", ref=None):

        # get type
        node_type = type(node)
        node_loc = None
        if node_type is Tracked:
            node_type = type(getattr(node, "_data"))
            node_loc = node.get_location()

        # get values
        value = str(node) if node_type in (int, float, complex, str) else ""
        type_name = node_type.__name__
        expr = str(node.get_expression()) if isinstance(node, Tracked) else ""

        # mark default values
        if node_loc and node_loc.id < 0 and len(value) and not len(expr):
            expr += "Default"

        # check for existing node
        if ref:

            # update tree item
            self.tree.item(ref, values=(value, type_name, expr))
            parent = ref
        else:

            # insert tree item
            parent = self.tree.insert(parent, "end", text=name, values=(value, type_name, expr), open=parent == "")

            # add values to node map
            if len(value):
                self.map[parent] = node

        # add children
        if hasattr(node_type, "SLOT_TYPES"):
            children = self.tree.get_children(parent)
            node_index = 0
            for attr, type_name in node_type.get_fields_and_field_types().items():
                self.tree_append(getattr(node, attr), attr, parent,
                                 children[node_index] if len(children) else None)
                node_index += 1

        # return reference
        return parent


class MonitorMain(ttk.Frame):

    def __init__(self, app, **kwargs):

        # init frame
        super().__init__(app, **kwargs)
        self.app = app

        # notebook
        self.tabs = ttk.Notebook(self)
        self.tab_state = StateTab(app, self.tabs)
        self.tab_log = LogTab(app, self.tabs)
        self.tabs.add(self.tab_state, text="State")
        self.tabs.add(self.tab_log, text="Log")
        self.tabs.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # topic panel
        self.frm_listen = ttk.Frame(self)

        # topic
        self.lbl_topic = ttk.Label(self.frm_listen, text="Topic")
        self.txt_topic = ttk.Entry(self.frm_listen, width=35)
        self.lbl_topic.columnconfigure(0, weight=1)
        self.txt_topic.columnconfigure(1, weight=1)
        self.txt_topic.insert(tk.END, "/topic")

        # type
        self.lbl_type = ttk.Label(self.frm_listen, text="Type")
        self.txt_type = ttk.Entry(self.frm_listen, width=35)
        self.lbl_type.columnconfigure(2, weight=1)
        self.txt_type.columnconfigure(3, weight=1)
        self.txt_type.insert(tk.END, "")
        self.txt_type.config(state="disabled")

        # listen button
        self.btn_listen = ttk.Button(self.frm_listen, text="Listen", command=self.action_listen)

        # value
        self.lbl_value = ttk.Label(self.frm_listen, text="Value")
        self.txt_value = ttk.Entry(self.frm_listen, width=35)
        self.btn_force = ttk.Button(self.frm_listen, text="Force", command=self.value_force)

        # grid setup
        self.lbl_topic.grid(row=0, column=0, sticky=tk.W + tk.E, padx=2, pady=4)
        self.txt_topic.grid(row=0, column=1, sticky=tk.W + tk.E, padx=2, pady=4)
        self.lbl_type.grid(row=1, column=0, sticky=tk.W + tk.E, padx=2, pady=4)
        self.txt_type.grid(row=1, column=1, sticky=tk.W + tk.E, padx=2, pady=4)
        self.btn_listen.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E, padx=2, pady=8)
        self.lbl_value.grid(row=1, column=3, sticky=tk.W + tk.E, padx=2, pady=4)
        self.txt_value.grid(row=1, column=4, sticky=tk.W + tk.E, padx=2, pady=4)
        self.btn_force.grid(row=2, column=3, columnspan=2, sticky=tk.W + tk.E, padx=2, pady=8)
        self.frm_listen.columnconfigure(2, minsize=50)
        self.frm_listen.pack(side=tk.BOTTOM, fill=tk.NONE, pady=2)

    def action_listen(self):
        if not self.app.node:
            messagebox.showerror(message="Node unavailable.")
            return
        if self.app.node.listen_status():
            self.btn_listen.configure(text="Listen")
            self.app.node.listen_stop()
        else:
            self.txt_type.config(state="enabled")
            self.txt_type.delete(0, tk.END)
            if not self.app.node.listen(self.txt_topic.get()):
                messagebox.showerror(message="Invalid topic.")
            else:
                self.txt_type.insert(0, self.app.node.msg_type.__name__)
                self.btn_listen.configure(text="Stop")
            self.txt_type.config(state="disabled")

    def value_force(self):
        self.tab_state.value_force(self.txt_value.get())


class Monitor(tk.Tk):

    def __init__(self, node):
        super().__init__()
        self.init_theme()

        # init node
        self.node = node

        # window config
        self.title("rosslt monitor")
        self.geometry("900x600")

        # add main frame
        MonitorMain(self).pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def init_theme(self):

        # default to built-in theme
        preferred_theme = "clam"
        s = ttk.Style(self)
        if preferred_theme in s.theme_names():
            s.theme_use(preferred_theme)

        # optionally load sv-ttk
        # noinspection PyBroadException
        try:
            import sv_ttk
            sv_ttk.set_theme("dark")
        except Exception:
            pass


def main(args=None):
    node = None

    # run node
    # noinspection PyBroadException
    try:
        rclpy.init(args=args)
        node = MonitorNode()
        thread = Thread(target=rclpy.spin, args=(node,))
        thread.start()
    except Exception:
        pass

    # create app
    app = Monitor(node)

    # process events
    app.mainloop()

    # exit
    try:
        rclpy.shutdown()
    except NameError:
        pass


if __name__ == "__main__":
    main()
