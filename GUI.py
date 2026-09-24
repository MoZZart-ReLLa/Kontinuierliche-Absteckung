import tkinter as tk
from tkinter import filedialog, ttk
import sys
from serial.tools import list_ports
from models import *
from algorithms import *
import state
from IO import Tachy



### locals ###

tachy1_port: str = None
tachy2_port: str = None

image_file_path: str = None


### Class definitions ###

class MainWindow:

	def __init__(self, root: tk.Tk):
		self.root = root
		self.root.title("Kontinuierliche Absteckung")
		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()
		self.root.geometry(f"{screen_width}x{screen_height}+0+0")

		self.toolbar = tk.Frame(self.root, padx=10, pady=10)
		self.toolbar.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.NW)

		# Stop button
		self.stop_button_frame = tk.Frame(self.toolbar, width=40, height=40)
		self.stop_button_frame.pack(anchor=tk.NW)
		self.stop_button_frame.pack_propagate(False)

		self.stop_button = tk.Button(
			self.stop_button_frame,
			text="■",
			fg="red",
			font=("TkDefaultFont", 16),
			anchor=tk.CENTER,
			justify=tk.CENTER,
			command=self.stop_all,
		)
		self.stop_button.pack(fill=tk.BOTH, expand=True)

		# Settings button
		self.settings_button_frame = tk.Frame(self.toolbar, width=40, height=40)
		self.settings_button_frame.pack(anchor=tk.NW)
		self.settings_button_frame.pack_propagate(False)

		self.settings_button = tk.Button(
			self.settings_button_frame,
			text="⚙",
			font=("TkDefaultFont", 20),
			anchor=tk.CENTER,
			justify=tk.CENTER,
			command=self.open_settings_window,
		)
		self.settings_button.pack(fill=tk.BOTH, expand=True)

		# Station button
		self.station_button_frame = tk.Frame(self.toolbar, width=40, height=40)
		self.station_button_frame.pack(anchor=tk.NW)
		self.station_button_frame.pack_propagate(False)

		self.station_button = tk.Button(
			self.station_button_frame,
			text="⌖",
			font=("TkDefaultFont", 28),
			anchor=tk.CENTER,
			justify=tk.CENTER,
			command=self.open_station_window,
		)
		self.station_button.pack(fill=tk.BOTH, expand=True)

		# Image button
		self.image_button_frame = tk.Frame(self.toolbar, width=40, height=40)
		self.image_button_frame.pack(anchor=tk.NW)
		self.image_button_frame.pack_propagate(False)

		self.image_button = tk.Button(
			self.image_button_frame,
			text="✎",
			font=("TkDefaultFont", 24),
			anchor=tk.CENTER,
			justify=tk.CENTER,
			command=self.select_image_file,
		)
		self.image_button.pack(fill=tk.BOTH, expand=True)

		# Canvas
		self.content = tk.Frame(self.root, padx=20, pady=20)
		self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
		self.canvas = tk.Canvas(self.content, background="white", highlightthickness=1)
		self.canvas.pack(fill=tk.BOTH, expand=True)
		self.lines = []


	def stop_all(self):
		state.tachy_1.stop()
		state.tachy_2.stop()


	def open_settings_window(self):
		settings_root = tk.Toplevel(self.root)
		SettingsWindow(settings_root, self)
		settings_root.transient(self.root)
		settings_root.grab_set()


	def open_station_window(self):
		station_root = tk.Toplevel(self.root)
		StationWindow(station_root, self)
		station_root.transient(self.root)
		station_root.grab_set()


	def select_image_file(self):
		global image_file_path

		selected_path = filedialog.askopenfilename(
			parent=self.root,
			filetypes=[("CSV-Dateien", "*.csv")],
		)
		if selected_path:
			self.draw_image(selected_path)
			image_file_path = selected_path


	def draw_image(self, file_path):
		self.lines = open_csv(file_path)

		# delete if empty
		if not self.lines:
			self.canvas.delete("all")
			return

		# calculate image size
		points = [point for line in self.lines for point in line.points]
		if not points:
			return

		canvas_width = max(self.canvas.winfo_width(), 1)
		canvas_height = max(self.canvas.winfo_height(), 1)
		margin = 20
		min_x = min(point.X for point in points)
		max_x = max(point.X for point in points)
		min_y = min(point.Y for point in points)
		max_y = max(point.Y for point in points)
		data_width = max(max_x - min_x, 1e-9)
		data_height = max(max_y - min_y, 1e-9)
		scale = min(
			(canvas_width - 2 * margin) / data_width,
			(canvas_height - 2 * margin) / data_height,
		)
		display_width = data_width * scale
		display_height = data_height * scale
		offset_x = (canvas_width - display_width) / 2
		offset_y = (canvas_height - display_height) / 2

		# draw lines
		self.canvas.delete("all")
		for line in self.lines:

			coordinates = []
			for point in line.points:
				coordinates.extend((offset_x + (point.X - min_x) * scale, offset_y + (max_y - point.Y) * scale))
			if len(coordinates) < 4:
				continue

			line_tag = f"line-{line.number}"

			self.canvas.create_line(
				*coordinates,
				fill="black",
				width=2,
				tags=(line_tag,)
			)
			self.canvas.tag_bind(
				line_tag,
				"<Enter>",
				lambda event, selected_tag=line_tag: self.canvas.itemconfigure(selected_tag, fill="red", width=4)
			)
			self.canvas.tag_bind(
				line_tag,
				"<Leave>",
				lambda event, selected_tag=line_tag: self.canvas.itemconfigure(selected_tag, fill="black", width=2)
			)
			self.canvas.tag_bind(
				line_tag,
				"<Button-1>",
				lambda event, selected_line=line: self.line_clicked(selected_line)
			)


	def line_clicked(self, line: Line):
		draw_line(line)



class SettingsWindow:

	def __init__(self, root: tk.Toplevel, main_window: MainWindow):
		self.root = root
		self.root.title("Einstellungen")
		self.root.geometry("520x330")
		self.root.minsize(520, 330)

		self.main_window = main_window

		self.content = tk.Frame(self.root, padx=20, pady=20)
		self.content.pack(fill=tk.BOTH, expand=True)

		tk.Label(self.content, text="Tachy 1").pack(anchor="w", pady=(0, 2))
		self.tachy1_port_combobox = ComPortSelector(self.content, tachy1_port)

		tk.Label(self.content, text="Tachy 2").pack(anchor="w", pady=(0, 2))
		self.tachy2_port_combobox = ComPortSelector(self.content, tachy2_port)

		tk.Label(self.content, text="Referenz").pack(anchor="w", pady=(0, 2))
		self.reference_prism_constant_entry = PrismTypeSelector(self.content, value=state.reference_prism_t)

		tk.Label(self.content, text="Rover").pack(anchor="w", pady=(0, 2))
		self.rover_prism_constant_entry = PrismTypeSelector(self.content, value=state.rover_prism_t)

		self.action_frame = tk.Frame(self.root)
		self.action_frame.pack(side=tk.BOTTOM, anchor=tk.E, padx=20, pady=15)
		tk.Button(self.action_frame, text="Abbruch", command=self.root.destroy).pack(side=tk.LEFT, padx=(0, 8))
		tk.Button(self.action_frame, text="Fertig", command=self.save_settings).pack(side=tk.LEFT)


	def save_settings(self):
		global tachy1_port, tachy2_port

		if tachy1_port != self.tachy1_port_combobox.get_device():	
			tachy1_port = self.tachy1_port_combobox.get_device()
			state.tachy_1 = Tachy(tachy1_port)

		if tachy2_port != self.tachy2_port_combobox.get_device():	
			tachy2_port = self.tachy2_port_combobox.get_device()
			state.tachy_2 = Tachy(tachy2_port)

		state.reference_prism_t = self.reference_prism_constant_entry.get_value()
		state.rover_prism_t = self.rover_prism_constant_entry.get_value()

		self.root.destroy()



class StationWindow:

	def __init__(self, root: tk.Toplevel, main_window: MainWindow):
		self.root = root
		self.root.title("Stationierung")
		self.root.geometry("900x320")
		self.root.minsize(900, 320)

		self.main_window = main_window

		self.content = tk.Frame(self.root, padx=20, pady=20)
		self.content.pack(fill=tk.BOTH, expand=True)
		self.content.columnconfigure(0, weight=1)
		self.content.columnconfigure(1, weight=1)
		self.content.columnconfigure(2, weight=1)
		self.content.columnconfigure(3, weight=1)

		# Tachy 1
		tk.Label(self.content, text="Tachy 1", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, padx=25, pady=(0, 18), sticky="w")

		self.tachy1_r1_button = MeasureButton("R1 messen", self.content, row=1, column=0, tachy=state.tachy_1)
		self.tachy1_r2_button = MeasureButton("R2 messen", self.content, row=2, column=0, tachy=state.tachy_1)
		self.tachy1_r3_button = MeasureButton("R3 messen", self.content, row=3, column=0, tachy=state.tachy_1)

		# Tachy 2
		tk.Label(self.content, text="Tachy 2", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=1, padx=25, pady=(0, 18), sticky="w")

		self.tachy2_r1_button = MeasureButton("R1 messen", self.content, row=1, column=1, tachy=state.tachy_2)
		self.tachy2_r2_button = MeasureButton("R2 messen", self.content, row=2, column=1, tachy=state.tachy_2)
		self.tachy2_r3_button = MeasureButton("R3 messen", self.content, row=3, column=1, tachy=state.tachy_2)

		#Reference prism setup
		tk.Label(self.content, text="Referenz", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=2, padx=25, pady=(0, 18), sticky="w")

		self.prism1_height_entry = FloatPlaceHolderEntry(self.content, width=20, placeholder="Höhe R1 [m]", row=1, column=2, value=state.prism1_height)
		self.prism2_height_entry = FloatPlaceHolderEntry(self.content, width=20, placeholder="Höhe R2 [m]", row=2, column=2, value=state.prism2_height)
		self.prism3_height_entry = FloatPlaceHolderEntry(self.content, width=20, placeholder="Höhe R3 [m]", row=3, column=2, value=state.prism3_height)

		# Rover prism setup
		tk.Label(self.content, text="Rover", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=3, padx=25, pady=(0, 18), sticky="w")

		self.rover_prism_height_entry = FloatPlaceHolderEntry(self.content, width=20, placeholder="Höhe [m]", row=1, column=3, value=state.rover_prism_height)

		# Cancel and Done buttons
		self.action_frame = tk.Frame(self.root)
		self.action_frame.pack(side=tk.BOTTOM, anchor=tk.E, padx=20, pady=15)

		self.cancel_button = tk.Button(
			self.action_frame,
			text="Abbruch",
			width=10,
			command=self.root.destroy
		)
		self.cancel_button.pack(side=tk.LEFT, padx=(0, 8))

		self.done_button = tk.Button(
			self.action_frame,
			text="Fertig", width=10,
			command=self.save_station_values
		)
		self.done_button.pack(side=tk.LEFT)


	def save_station_values(self):

		def correct_height(point: Point, height: float):
			point.Z -= height

			return point

		state.prism1_height = self.prism1_height_entry.get_value()
		state.prism2_height = self.prism2_height_entry.get_value()
		state.prism3_height = self.prism3_height_entry.get_value()
		state.rover_prism_height = self.rover_prism_height_entry.get_value()

		T1P1 = self.tachy1_r1_button.get_value()
		T1P2 = self.tachy1_r2_button.get_value()
		T1P3 = self.tachy1_r3_button.get_value()
		T2P1 = self.tachy2_r1_button.get_value()
		T2P2 = self.tachy2_r2_button.get_value()
		T2P3 = self.tachy2_r3_button.get_value()

		if state.tachy_1 is not None and state.tachy_2 is not None:
			adjust_station(correct_height(T1P1, state.prism1_height),
						   correct_height(T1P2, state.prism2_height),
						   correct_height(T1P3, state.prism3_height),
						   correct_height(T2P1, state.prism1_height),
						   correct_height(T2P2, state.prism2_height),
						   correct_height(T2P3, state.prism3_height))
		elif state.tachy_1:
				state.P1 = correct_height(T1P1, state.prism1_height)
				state.P2 = correct_height(T1P2, state.prism2_height)
				state.P3 = correct_height(T1P3, state.prism3_height)
		elif state.tachy_2:
				state.P1 = correct_height(T2P1, state.prism1_height)
				state.P2 = correct_height(T2P2, state.prism2_height)
				state.P3 = correct_height(T2P3, state.prism3_height)

		calculate_image_trafo()

		self.root.destroy()



### Entry class definitions ###

class MeasureButton(tk.Frame):

	def __init__(self, text, master=None, row=None, column=None, tachy=None):
		super().__init__(master)

		self.position = None
		self.tachy = tachy

		self.measure_button = tk.Button(
			self,
			text=text,
			width=11,
			bg="gray",
			activebackground="gray",
			state=tk.NORMAL if tachy is not None else tk.DISABLED,
			command=self.do_measurement,
		)
		self.measure_button.pack(side=tk.LEFT)
		if row is not None and column is not None:
			self.grid(row=row, column=column, padx=25, pady=10, sticky="w")


	def do_measurement(self):
		self.position = self.tachy.two_face_measurement(state.reference_prism_t)

		if self.position != None:
			self.measure_button.configure(bg="green", activebackground="green")
		else:
			self.measure_button.configure(bg="red", activebackground="red")


	def get_value(self) -> Point|None:
		return self.position



class FloatPlaceHolderEntry(tk.Entry):

	def __init__(self, master=None, placeholder="", placeholder_color="gray", text_color="black", row=None, column=None, value=None, **kwargs):
		super().__init__(master, **kwargs)

		if row is not None and column is not None:
			self.grid(row=row, column=column, padx=25, pady=10, sticky="w")

		self.placeholder = placeholder
		self.placeholder_color = placeholder_color
		self.default_fg = text_color
		self._is_placeholder_active = False

		vcmd = (self.register(self._validate_input), "%P")
		self.configure(validate="key", validatecommand=vcmd)
		self.bind("<FocusIn>", self._on_focus_in)
		self.bind("<FocusOut>", self._on_focus_out)
		self.set_value(value)

	def _validate_input(self, new_val):
		if self._is_placeholder_active or new_val == self.placeholder:
			return True
		if new_val in ("", "-", ".", ",", "-.", "-,"):
			return True
		try:
			float(new_val.replace(",", "."))
			return True
		except ValueError:
			return False

	def _show_placeholder(self):
		self._is_placeholder_active = True
		self.delete(0, tk.END)
		self.insert(0, self.placeholder)
		self.configure(fg=self.placeholder_color)
		self._is_placeholder_active = False

	def _on_focus_in(self, event):
		if self.cget("fg") == self.placeholder_color:
			self._is_placeholder_active = True
			self.delete(0, tk.END)
			self.configure(fg=self.default_fg)
			self._is_placeholder_active = False

	def _on_focus_out(self, event):
		if not self.get().strip():
			self._show_placeholder()

	def get_value(self) -> float | None:
		if self.cget("fg") == self.placeholder_color:
			return None
		val_str = self.get().strip().replace(",", ".")
		try:
			return float(val_str)
		except ValueError:
			return None

	def set_value(self, value):
		self._is_placeholder_active = True
		self.delete(0, tk.END)
		if value is not None and str(value).strip() != "":
			try:
				num = float(str(value).replace(",", "."))
				display_str = str(int(num)) if num.is_integer() else str(num)
				self.insert(0, display_str)
				self.configure(fg=self.default_fg)
			except ValueError:
				self._show_placeholder()
		else:
			self._show_placeholder()
		self._is_placeholder_active = False




class ComPortSelector(ttk.Combobox):

	def __init__(self, master, value=None):
		self.display_to_device = {}
		port_displays = []
		available_ports = list(list_ports.comports())
		if sys.platform.startswith("linux"):
			available_ports = [
				port
				for port in available_ports
				if port.device.startswith(("/dev/ttyUSB", "/dev/ttyACM", "/dev/rfcomm"))
			]
		for port in available_ports:
			info = [port.device]
			if port.description and port.description != "n/a":
				info.append(port.description)
			if port.manufacturer and port.manufacturer not in info:
				info.append(port.manufacturer)
			if len(info) == 1 and port.hwid and port.hwid != "n/a":
				info.append(port.hwid)
			display = " - ".join(info)
			port_displays.append(display)
			self.display_to_device[display] = port.device

		super().__init__(master, values=port_displays, state="readonly", width=48)
		if value:
			self.set(next((display for display, device in self.display_to_device.items() if device == value), value))
		self.pack(anchor="w", pady=(0, 10))


	def get_device(self):
		return self.display_to_device.get(self.get())



class PrismTypeSelector(ttk.Combobox):

	def __init__(self, master, value=None):
		self.display_to_type = {f"{prism_type.name}": prism_type for prism_type in PRISMTYPE}
		self.none_display = "None"
		super().__init__(
			master,
			values=[self.none_display, *self.display_to_type],
			state="readonly",
			width=28,
		)
		self.set_value(value)
		self.pack(anchor="w", pady=(0, 10))

	def set_value(self, value):
		if value is None:
			self.set(self.none_display)
			return
		for display, prism_type in self.display_to_type.items():
			if prism_type == value:
				self.set(display)
				return
		self.set(self.none_display)

	def get_value(self):
		if self.get() == self.none_display:
			return None
		return self.display_to_type.get(self.get())