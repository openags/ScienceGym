"""Construct a depth buffer whose samples match the pixel-centre camera model."""
import mujoco


def depth_renderer(model, height, width):
    # MSAA depth resolve can select a subpixel sample; unprojecting it at the
    # pixel centre biases narrow surfaces. This controls the depth context
    # only. Restore the model setting before creating an RGB/video context.
    previous = int(model.vis.quality.offsamples)
    try:
        model.vis.quality.offsamples = 0
        renderer = mujoco.Renderer(model, height=height, width=width,
                                   max_geom=model.ngeom+1000)
    finally:
        model.vis.quality.offsamples = previous
    renderer.enable_depth_rendering()
    return renderer
