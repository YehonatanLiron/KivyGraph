from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics import Mesh
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.properties import ListProperty, ReferenceListProperty, \
        StringProperty, BoundedNumericProperty, BooleanProperty
from kivy.lang import Builder

Builder.load_file('graph_layout.kv')

MAX_NUM_MESH_VERTICES = 30000
TARGET_DATA_LENGTH = 45000
MIN_DILUTION_FACTOR = 8


class GraphLayout(ScatterLayout):
    data = ListProperty(None)
    x_data = ListProperty(None)
    texture_file = StringProperty()
    start_r = BoundedNumericProperty(62, min=0, max=255)
    start_g = BoundedNumericProperty(184, min=0, max=255)
    start_b = BoundedNumericProperty(186, min=0, max=255)
    start_texture = ReferenceListProperty(start_r, start_g, start_b)
    end_r = BoundedNumericProperty(62, min=0, max=255)
    end_g = BoundedNumericProperty(101, min=0, max=255)
    end_b = BoundedNumericProperty(183, min=0, max=255)
    end_texture = ReferenceListProperty(end_r, end_g, end_b)
    opacity = BoundedNumericProperty(1.0, min=0.0, max=1.0)
    normalize = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(GraphLayout, self).__init__(**kwargs)
        self.previousX = -1
        self.start_offset = 0
        self.zoom = 1.0
        self.zero_vec = [0] * MAX_NUM_MESH_VERTICES * 2
        self.pace_factor = 1

        self.bind(data=self.update_layout)

        try:
            self.texture = CoreImage(self.texture_file).texture
        except AttributeError:
            self.texture = Texture.create(size=self.size)
            self.calculate_background_texture_blit()

        with self.canvas:
            self.pos_mesh_0 = Mesh(texture=self.texture, mode='triangle_strip')
            self.pos_mesh_1 = Mesh(texture=self.texture, mode='triangle_strip')
            self.neg_mesh_0 = Mesh(texture=self.texture, mode='triangle_strip')
            self.neg_mesh_1 = Mesh(texture=self.texture, mode='triangle_strip')
            self.update_layout()

    def update_layout(self, *args):
        if self.data:
            self.enable_layout()
        else:
            self.disable_layout()

    def disable_layout(self, *args):
        self.unbind(size=self.update_size)
        self.on_touch_down = self.nop
        self.on_touch_up = self.nop
        self.on_touch_move = self.nop
        self.bind(size=self.nop)
        self.positive_points = []
        self.negative_points = []

        self.update_mesh()

    def enable_layout(self, *args):
        self.on_touch_down = self.on_touch_down_active
        self.on_touch_up = self.on_touch_up_active
        self.on_touch_move = self.on_touch_move_active
        self.unbind(size=self.nop)
        self.bind(size=self.update_size)

        self.previousX = -1
        self.start_offset = 0
        self.zoom = 1.0
        self.y_raw_data = self.data
        self.raw_data_length = len(self.y_raw_data)

        self.dilution_factor = max(MIN_DILUTION_FACTOR, int(round(float(self.raw_data_length) / TARGET_DATA_LENGTH)))

        self.y_data = self.dilute_data()

        self.create_data_lists()

        self.create_mesh_index_vectors()

        self.data_length = len(self.y_data)

        self.maximal_display_data_length = min(self.data_length, 2*MAX_NUM_MESH_VERTICES)

        # run more than once

        self.update_size()

    def nop(self, *args):
        pass

    def update_size(self, *args):
        self.display_data_length_float = float(self.maximal_display_data_length) / self.zoom
        self.display_data_length = int(self.display_data_length_float)

        self.x_data = [((x * self.width) / self.display_data_length_float) for x in
                       range(0, self.display_data_length)]

        self.end_offset = min(self.data_length, self.display_data_length + self.start_offset)

        self.create_indexes_for_display()

        self.scale_to_layout()

        self.create_x_y_texture_lists_for_display()

        self.create_vertex_lists()

        self.update_mesh()

    def calculate_background_texture_blit(self):
        h = int(self.height)
        x = range(h)

        global color_list
        color_list = []

        def create_color_list(x):
            global color_list
            color_r = int(self.start_texture[0] + (self.end_texture[0] - self.start_texture[0]) * float(x) / h)
            color_g = int(self.start_texture[1] + (self.end_texture[1] - self.start_texture[1]) * float(x) / h)
            color_b = int(self.start_texture[2] + (self.end_texture[2] - self.start_texture[2]) * float(x) / h)

            trio = [color_r, color_g, color_b] * int(self.width)
            color_list = color_list + trio

        map(create_color_list, x)

        buf = b''.join(map(chr, color_list))
        del color_list
        self.texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

    def on_touch_down_active(self, touch):
        touch.grab(self)

        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown': ## zoom in
                self.zoom = self.zoom * 1.1

            elif touch.button == 'scrollup': ## zoom out
                self.zoom = max(1.0, self.zoom * 0.9)

            self.update_size()

        return False

    def on_touch_up_active(self, touch):
        self.previousX = -1
        return False

    def on_touch_move_active(self, touch):
        if self.previousX == -1:
            self.previousX = touch.x
        else:

            diff = int(self.pace_factor * 16 * (self.previousX - touch.x) / self.zoom)

            prev_start_offset = self.start_offset

            self.start_offset = max(0, int(self.start_offset + diff))

            if prev_start_offset == self.start_offset:
                return False

            self.end_offset = min(self.data_length, self.display_data_length + self.start_offset)

            self.create_indexes_for_display()

            self.create_x_y_texture_lists_for_display()

            self.create_vertex_lists()

            self.update_mesh()

            self.previousX = touch.x
        return False

    # Run Once per data

    def dilute_data(self):
        return self.y_raw_data[::self.dilution_factor]

    def create_data_lists(self):
        if self.normalize:
            mean = sum(self.y_data) / len(self.y_data)
            self.zero_centered_y_list = [y - mean for y in self.y_data]
        else:
            self.zero_centered_y_list = self.y_data

        abs_max_of_zero_centered_y = max(max(self.zero_centered_y_list), -min(self.zero_centered_y_list))

        self.y_scaled_to_1_list = [float(y) / abs_max_of_zero_centered_y for y in self.zero_centered_y_list]
        self.texture_list = [abs(x) for x in self.y_scaled_to_1_list]
        self.y_scaled_to_1_centered_list = [y + 1 for y in self.y_scaled_to_1_list]

    def create_mesh_index_vectors(self):
        pos_index = []
        neg_index = []

        def get_pos_neg_index((i, v)):
            if v >= 0:
                pos_index.append(i)
            else:
                neg_index.append(i)

        map(get_pos_neg_index, enumerate(self.y_data))
        self.pos_index = pos_index
        self.neg_index = neg_index

    # Run for adjustments

    def create_indexes_for_display(self):
        self.pos_index_display = list(filter(lambda x: x >= self.start_offset and x < self.end_offset, self.pos_index))
        self.neg_index_display = list(filter(lambda x: x >= self.start_offset and x < self.end_offset, self.neg_index))

    def scale_to_layout(self):
        self.y_scaled_to_layout_list = [y * self.height * 0.5 for y in self.y_scaled_to_1_centered_list]

    def create_x_y_texture_lists_for_display(self):
        self.y_pos_display_list = [self.y_scaled_to_layout_list[i] for i in self.pos_index_display]
        self.x_pos_display_list = [self.x_data[i - self.start_offset] for i in self.pos_index_display]
        self.t_pos_display_list = [self.texture_list[i] for i in self.pos_index_display]

        self.y_neg_display_list = [self.y_scaled_to_layout_list[i] for i in self.neg_index_display]
        self.x_neg_display_list = [self.x_data[i - self.start_offset] for i in self.neg_index_display]
        self.t_neg_display_list = [self.texture_list[i] for i in self.neg_index_display]

    def create_vertex_lists(self):
        pos_length = len(self.x_pos_display_list)
        self.positive_points = [0] * 8 * pos_length
        self.positive_points[0::8] = self.x_pos_display_list
        self.positive_points[1::8] = [self.height / 2] * pos_length
        self.positive_points[4::8] = self.x_pos_display_list
        self.positive_points[5::8] = self.y_pos_display_list
        self.positive_points[7::8] = self.t_pos_display_list

        neg_length = len(self.x_neg_display_list)
        self.negative_points = [0] * 8 * neg_length
        self.negative_points[0::8] = self.x_neg_display_list
        self.negative_points[1::8] = [self.height / 2] * neg_length
        self.negative_points[4::8] = self.x_neg_display_list
        self.negative_points[5::8] = self.y_neg_display_list
        self.negative_points[7::8] = self.t_neg_display_list

    def update_mesh(self):
        positive_points_0 = self.positive_points[0:MAX_NUM_MESH_VERTICES * 8]
        num_of_vertices = len(positive_points_0) / 4
        positive_indices_0 = range(num_of_vertices)

        positive_points_1 = self.positive_points[MAX_NUM_MESH_VERTICES * 8: MAX_NUM_MESH_VERTICES * 8 * 2]
        num_of_vertices = len(positive_points_1) / 4
        positive_indices_1 = range(num_of_vertices)

        negative_points_0 = self.negative_points[0:MAX_NUM_MESH_VERTICES * 8]
        num_of_vertices = len(negative_points_0) / 4
        negative_indices_0 = range(num_of_vertices)

        negative_points_1 = self.negative_points[MAX_NUM_MESH_VERTICES * 8: MAX_NUM_MESH_VERTICES * 8 * 2]
        num_of_vertices = len(negative_points_1) / 4
        negative_indices_1 = range(num_of_vertices)

        try:
            self.pos_mesh_0.indices = positive_indices_0
            self.pos_mesh_0.vertices = positive_points_0

            self.pos_mesh_1.indices = positive_indices_1
            self.pos_mesh_1.vertices = positive_points_1

            self.neg_mesh_0.indices = negative_indices_0
            self.neg_mesh_0.vertices = negative_points_0

            self.neg_mesh_1.indices = negative_indices_1
            self.neg_mesh_1.vertices = negative_points_1
        except AttributeError:
            pass
