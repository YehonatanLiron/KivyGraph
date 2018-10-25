from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty, ObjectProperty, BoundedNumericProperty, BooleanProperty
from graph_layout import GraphLayout
from kivy.lang import Builder
from kivy.graphics import Line
from kivy.graphics import Color
from kivy.uix.label import Label
from utility_functions import linspace

Builder.load_file('graph_box.kv')
MAX_FONT_SIZE = 18


class GraphBox(FloatLayout):
    y_data = ListProperty(None)
    borderWidth = ObjectProperty(0)
    number_of_lines = BoundedNumericProperty(5, min=0, max=6)
    y_grid_values = BooleanProperty(False)
    opacity = BoundedNumericProperty(1.0, min=0.0, max=1.0)
    normalize = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(GraphBox, self).__init__(**kwargs)

        if self.number_of_lines%2 == 1:
            self.number_of_lines = self.number_of_lines+1

        self.total_inner_box_size = self.size[0] - 2 * self.borderWidth, self.size[1] - 2 * self.borderWidth
        self.graph_layout_pos = (0.1 * self.total_inner_box_size[0] + self.pos[0] + self. borderWidth,
                                self.pos[1] + self.borderWidth)
        self.graph_layout_size = 0.9 * self.total_inner_box_size[0], self.total_inner_box_size[1]

        self.graph_layout = GraphLayout(
            data=self.y_data,
            size_hint=(None, None),
            pos=self.graph_layout_pos,
            size=self.graph_layout_size,
            do_translation_y=False,
            normalize=self.normalize,
            opacity=self.opacity
        )

        self.add_widget(self.graph_layout)

        self.bind(size=self.update_layout)
        self.bind(pos=self.update_layout)
        self.bind(y_data=self.update_data)

        self.lines = dict()

        if self.y_grid_values:
            self.labels = dict()

            for i in range(1, self.number_of_lines):
                label_name = str(i)
                self.labels[label_name] = Label(
                    color=(0, 0, 0, 0.5),
                    pos_hint={'x': -0.45, 'y': float(i)/self.number_of_lines-0.5},
                    font_size=min(MAX_FONT_SIZE, int(0.065*self.height))
                )
                self.add_widget(self.labels[label_name])

            self.update_y_grid_labels()

        with self.canvas:
            Color(0, 0, 0, 0.5)
            for i in range(1, self.number_of_lines):
                line_name = str(i)
                self.lines[line_name] = Line(points=[
                    (self.graph_layout_pos[0], self.graph_layout_pos[1] + self.graph_layout_size[1]*i/self.number_of_lines),
                    (self.graph_layout_pos[0] + self.graph_layout_size[0], self.graph_layout_pos[1] + self.graph_layout_size[1]*i/self.number_of_lines)],
                    width=0.5
                )

    def update_layout(self, *args):
        self.total_inner_box_size = self.size[0] - 2 * self.borderWidth, self.size[1] - 2 * self.borderWidth

        self.graph_layout_pos = (0.1 * self.total_inner_box_size[0] + self.pos[0] + self. borderWidth,
                                self.pos[1] + self.borderWidth)
        self.graph_layout_size = 0.9 * self.total_inner_box_size[0], self.total_inner_box_size[1]

        self.graph_layout.size = self.graph_layout_size
        self.graph_layout.pos = self.graph_layout_pos

        for i in range(1, self.number_of_lines):
            line_name = str(i)

            self.lines[line_name].points = [
                (self.graph_layout_pos[0], self.graph_layout_pos[1] + self.graph_layout_size[1] * i / self.number_of_lines),
                (self.graph_layout_pos[0] + self.graph_layout_size[0], self.graph_layout_pos[1] + self.graph_layout_size[1] * i / self.number_of_lines)
            ]
            try:
                self.labels[line_name].font_size = min(MAX_FONT_SIZE, int(0.065*self.height))
            except AttributeError:
                pass

    def update_y_grid_labels(self):
        if self.y_data:
            max_data = max(max(self.y_data), -min(self.y_data))
            label_values = linspace(-max_data, max_data, self.number_of_lines+1)

            for i in range(1, self.number_of_lines):
                label_name = str(i)
                self.labels[label_name].text = str("%.2E" % label_values[i])
        else:
            for i in range(1, self.number_of_lines):
                label_name = str(i)
                self.labels[label_name].text = "000"

    def update_data(self, *args):
        if self.y_grid_values:
            self.update_y_grid_labels()
        self.graph_layout.data = self.y_data


