from slmsuite.hardware.cameras.camera import Camera

try:
    from ximea import xiapi
except ModuleNotFoundError:
    raise ImportError(
        "Ximea xiapi not installed. See https://www.ximea.com/support/wiki/apis/APIs"
    )


class Ximea(Camera):
    def __init__(
        self,
        serial=None,
        pitch_um=None,
        verbose=True,
        **kwargs
    ):
        if verbose:
            print("Initializing Ximea camera... ", end="")

        self.cam = xiapi.Camera()

        # Open camera
        if serial is None:
            self.cam.open_device()
        else:
            self.cam.open_device_by_SN(serial)

        # Create image container
        self.image = xiapi.Image()

        # Start acquisition
        self.cam.start_acquisition()

        # Grab one frame to initialize metadata
        self.cam.get_image(self.image)

        width = self.image.width
        height = self.image.height

        try:
            bitdepth_str = self.cam.get_output_bit_depth()
            bitdepth = int(bitdepth_str.split("_")[-1])
        except Exception:
            bitdepth = 8

        super().__init__(
            (width, height),
            bitdepth=bitdepth,
            pitch_um=pitch_um,
            name=serial,
            **kwargs
        )

        if verbose:
            print("success")

    def close(self):
        self.cam.stop_acquisition()
        self.cam.close_device()

    @staticmethod
    def info(verbose=True):
        """Return list of available camera serials."""
        serials = []
        index = 0

        while True:
            cam = xiapi.Camera()
            try:
                cam.open_device_by_index(index)
                serial = cam.get_device_sn()
                serials.append(serial)
                cam.close_device()
                index += 1
            except Exception:
                break

        if verbose:
            print("Detected cameras:", serials)

        return serials

    ### Exposure ###

    def _get_exposure_hw(self):
        # exposure is in microseconds
        return self.cam.get_exposure() / 1e6

    def _set_exposure_hw(self, exposure_s):
        self.cam.set_exposure(int(exposure_s * 1e6))

    ### Image acquisition ###

    def _get_image_hw(self, timeout_s):
        timeout_ms = int(timeout_s * 1000)

        self.cam.get_image(self.image, timeout=timeout_ms)

        return self.image.get_image_data_numpy()

    ### Optional: WOI (crop) ###

    def set_woi(self, woi=None):
        """
        woi = (x, width, y, height)
        """
        if woi is None:
            return

        x, w, y, h = woi

        self.cam.set_offsetX(x)
        self.cam.set_width(w)
        self.cam.set_offsetY(y)
        self.cam.set_height(h)