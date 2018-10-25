from kivy.app import App
from math import sin, cos
from graph_box import GraphBox

from kivy.properties import ListProperty


class DrawingLineApp(App):
    y_data = ListProperty(None)

    def build(self):
        return GraphBox(y_data=self.y_data, y_grid_values=True)


if __name__ == "__main__":
    # data = [((50 * sin(float(x)/100) + 50)*cos(x/20) * x/200) for x in range(0, 200000)]
    data = [(x * x * sin(x / 100)) for x in range(0, 710000)]

    DrawingLineApp(y_data=data).run()
