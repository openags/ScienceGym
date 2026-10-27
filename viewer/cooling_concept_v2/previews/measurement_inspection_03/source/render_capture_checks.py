"""Reject empty browser captures before treating them as inspection evidence."""
import base64
import io
from PIL import Image,ImageStat


def save_checked_jpeg(encoded,path):
    data=base64.b64decode(encoded)
    with Image.open(io.BytesIO(data)) as image:
        image.load();stats=ImageStat.Stat(image.convert('RGB'))
        if max(stats.stddev)<1.:
            raise RuntimeError('Uniform/empty render rejected: '+str(path))
        quality=dict(mean_rgb=stats.mean,stddev_rgb=stats.stddev,resolution=list(image.size))
    path.write_bytes(data)
    return quality
