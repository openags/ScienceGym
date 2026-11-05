"""Native tool-observation cameras shared by recording and independent replay."""
import mujoco
from sensor_rendering import depth_renderer


class ToolCameras:
    def __init__(self,model):
        self.rgb=mujoco.Renderer(model,height=480,width=640,max_geom=model.ngeom+1000)
        self.depth=depth_renderer(model,480,640)
        self.option=mujoco.MjvOption();self.option.geomgroup[3]=0;self.option.sitegroup[:]=0

    def read(self,data):
        self.rgb.update_scene(data,camera='head_rgb',scene_option=self.option)
        rgb=self.rgb.render().copy()
        self.depth.update_scene(data,camera='head_depth',scene_option=self.option)
        return dict(head_rgb=rgb,head_depth=self.depth.render().copy())

    def close(self):
        self.rgb.close();self.depth.close()
