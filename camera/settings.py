import depthai as dai
from typing import Dict, Any


class CameraSettingsManager:
    """Manages camera settings and control commands"""

    # Setting constraints
    EXPOSURE_MIN = 1
    EXPOSURE_MAX = 33000
    ISO_MIN = 100
    ISO_MAX = 1600
    FOCUS_MIN = 0
    FOCUS_MAX = 255
    BRIGHTNESS_MIN = -10
    BRIGHTNESS_MAX = 10
    CONTRAST_MIN = -10
    CONTRAST_MAX = 10
    SATURATION_MIN = -10
    SATURATION_MAX = 10
    SHARPNESS_MIN = 0
    SHARPNESS_MAX = 4
    WB_MIN = 1000
    WB_MAX = 12000

    def __init__(self, camera_controller):
        self.camera_controller = camera_controller

        # Camera settings with default values
        self.settings: Dict[str, Any] = {
            "exposure": 20000,
            "iso": 800,
            "focus": 130,
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "sharpness": 1,
            "white_balance": 4000,
            "fps": 30,
            "resolution_width": 1280,
            "resolution_height": 720,
            "luma_denoise": 1,
            "chroma_denoise": 1,
            # App-level setting: GPS-based capture interval threshold (meters)
            "gps_interval_m": 1.0,
        }

        # Auto mode flags
        self.auto_modes: Dict[str, bool] = {
            "auto_exposure": True,
            "auto_focus": True,
            "auto_white_balance": True,
            "auto_exposure_lock": False,
            "auto_white_balance_lock": False,
        }

    def _clamp(self, value: int, min_val: int, max_val: int) -> int:
        """Clamp value between min and max"""
        return max(min_val, min(value, max_val))

    def set_auto_exposure(self, enabled: bool):
        """Set auto exposure mode"""
        self.auto_modes["auto_exposure"] = enabled
        ctrl = dai.CameraControl()

        if enabled:
            ctrl.setAutoExposureEnable()
        else:
            ctrl.setManualExposure(self.settings["exposure"], self.settings["iso"])

        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_auto_focus(self, enabled: bool):
        """Set auto focus mode"""
        self.auto_modes["auto_focus"] = enabled
        ctrl = dai.CameraControl()

        if enabled:
            ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.CONTINUOUS_VIDEO)
        else:
            ctrl.setManualFocus(self.settings["focus"])

        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_auto_white_balance(self, enabled: bool):
        """Set auto white balance mode"""
        self.auto_modes["auto_white_balance"] = enabled
        ctrl = dai.CameraControl()

        if enabled:
            ctrl.setAutoWhiteBalanceMode(dai.CameraControl.AutoWhiteBalanceMode.AUTO)
        else:
            ctrl.setManualWhiteBalance(self.settings["white_balance"])

        self.camera_controller.send_control_to_all_cameras(ctrl)

    def trigger_autofocus(self):
        """Trigger one-time autofocus"""
        ctrl = dai.CameraControl()
        ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.AUTO)
        ctrl.setAutoFocusTrigger()
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_exposure(self, value: int):
        """Set manual exposure"""
        self.settings["exposure"] = self._clamp(
            value, self.EXPOSURE_MIN, self.EXPOSURE_MAX
        )
        if not self.auto_modes["auto_exposure"]:
            ctrl = dai.CameraControl()
            ctrl.setManualExposure(self.settings["exposure"], self.settings["iso"])
            self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_iso(self, value: int):
        """Set ISO value"""
        self.settings["iso"] = self._clamp(value, self.ISO_MIN, self.ISO_MAX)
        if not self.auto_modes["auto_exposure"]:
            ctrl = dai.CameraControl()
            ctrl.setManualExposure(self.settings["exposure"], self.settings["iso"])
            self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_focus(self, value: int):
        """Set manual focus"""
        self.settings["focus"] = self._clamp(value, self.FOCUS_MIN, self.FOCUS_MAX)
        if not self.auto_modes["auto_focus"]:
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(self.settings["focus"])
            self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_brightness(self, value: int):
        """Set brightness"""
        self.settings["brightness"] = self._clamp(
            value, self.BRIGHTNESS_MIN, self.BRIGHTNESS_MAX
        )
        ctrl = dai.CameraControl()
        ctrl.setBrightness(self.settings["brightness"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_contrast(self, value: int):
        """Set contrast"""
        self.settings["contrast"] = self._clamp(
            value, self.CONTRAST_MIN, self.CONTRAST_MAX
        )
        ctrl = dai.CameraControl()
        ctrl.setContrast(self.settings["contrast"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_saturation(self, value: int):
        """Set saturation"""
        self.settings["saturation"] = self._clamp(
            value, self.SATURATION_MIN, self.SATURATION_MAX
        )
        ctrl = dai.CameraControl()
        ctrl.setSaturation(self.settings["saturation"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_sharpness(self, value: int):
        """Set sharpness"""
        self.settings["sharpness"] = self._clamp(
            value, self.SHARPNESS_MIN, self.SHARPNESS_MAX
        )
        ctrl = dai.CameraControl()
        ctrl.setSharpness(self.settings["sharpness"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_white_balance(self, value: int):
        """Set manual white balance"""
        self.settings["white_balance"] = self._clamp(value, self.WB_MIN, self.WB_MAX)
        if not self.auto_modes["auto_white_balance"]:
            ctrl = dai.CameraControl()
            ctrl.setManualWhiteBalance(self.settings["white_balance"])
            self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_luma_denoise(self, value: int):
        """Set luma denoise level"""
        self.settings["luma_denoise"] = self._clamp(value, 0, 4)
        ctrl = dai.CameraControl()
        ctrl.setLumaDenoise(self.settings["luma_denoise"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_chroma_denoise(self, value: int):
        """Set chroma denoise level"""
        self.settings["chroma_denoise"] = self._clamp(value, 0, 4)
        ctrl = dai.CameraControl()
        ctrl.setChromaDenoise(self.settings["chroma_denoise"])
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_auto_exposure_lock(self, locked: bool):
        """Set auto exposure lock"""
        self.auto_modes["auto_exposure_lock"] = locked
        ctrl = dai.CameraControl()
        ctrl.setAutoExposureLock(locked)
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_auto_white_balance_lock(self, locked: bool):
        """Set auto white balance lock"""
        self.auto_modes["auto_white_balance_lock"] = locked
        ctrl = dai.CameraControl()
        ctrl.setAutoWhiteBalanceLock(locked)
        self.camera_controller.send_control_to_all_cameras(ctrl)

    def set_anti_banding_mode(self, mode_index: int):
        """Set anti-banding mode"""
        try:
            anti_banding_modes = list(
                dai.CameraControl.AntiBandingMode.__members__.values()
            )
            if 0 <= mode_index < len(anti_banding_modes):
                ctrl = dai.CameraControl()
                ctrl.setAntiBandingMode(anti_banding_modes[mode_index])
                self.camera_controller.send_control_to_all_cameras(ctrl)
        except Exception as e:
            print(f"Anti-banding mode error: {e}")

    def set_effect_mode(self, mode_index: int):
        """Set camera effect mode"""
        try:
            effect_modes = list(dai.CameraControl.EffectMode.__members__.values())
            if 0 <= mode_index < len(effect_modes):
                ctrl = dai.CameraControl()
                ctrl.setEffectMode(effect_modes[mode_index])
                self.camera_controller.send_control_to_all_cameras(ctrl)
        except Exception as e:
            print(f"Effect mode error: {e}")

    def get_setting(self, key: str) -> Any:
        """Get setting value"""
        value = self.settings.get(key, 0)
        # Ensure integer values for camera controls
        if key in ["exposure", "iso", "focus", "brightness", "contrast", "saturation", "sharpness", "white_balance", "luma_denoise", "chroma_denoise"]:
            return int(value) if value is not None else 0
        return value

    def get_auto_mode(self, key: str) -> bool:
        """Get auto mode status"""
        return self.auto_modes.get(key, False)

    def update_setting(self, key: str, value: Any):
        """Update setting value without applying to camera"""
        if key in self.settings:
            self.settings[key] = value

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self.settings.copy()

    def get_all_auto_modes(self) -> Dict[str, bool]:
        """Get all auto mode statuses"""
        return self.auto_modes.copy()

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.settings.update(
            {
                "exposure": 20000,
                "iso": 800,
                "focus": 130,
                "brightness": 0,
                "contrast": 0,
                "saturation": 0,
                "sharpness": 1,
                "white_balance": 4000,
                "luma_denoise": 1,
                "chroma_denoise": 1,
            }
        )

        self.auto_modes.update(
            {
                "auto_exposure": True,
                "auto_focus": True,
                "auto_white_balance": True,
                "auto_exposure_lock": False,
                "auto_white_balance_lock": False,
            }
        )

        # Apply defaults to cameras
        self.apply_all_settings()

    def apply_all_settings(self):
        """Apply all current settings to cameras"""
        print("Applying camera settings...")
        
        # Apply auto modes
        self.set_auto_exposure(self.auto_modes["auto_exposure"])
        self.set_auto_focus(self.auto_modes["auto_focus"])
        self.set_auto_white_balance(self.auto_modes["auto_white_balance"])

        # Apply manual settings
        self.set_brightness(self.settings["brightness"])
        self.set_contrast(self.settings["contrast"])
        self.set_saturation(self.settings["saturation"])
        self.set_sharpness(self.settings["sharpness"])
        self.set_luma_denoise(self.settings["luma_denoise"])
        self.set_chroma_denoise(self.settings["chroma_denoise"])

        # Apply locks
        self.set_auto_exposure_lock(self.auto_modes["auto_exposure_lock"])
        self.set_auto_white_balance_lock(self.auto_modes["auto_white_balance_lock"])
        
        print("Camera settings applied successfully!")
        
        # Log current settings
        print("Current camera settings:")
        for key, value in self.settings.items():
            if key in ["exposure", "iso", "focus", "brightness", "contrast", "saturation", "sharpness", "white_balance", "luma_denoise", "chroma_denoise"]:
                print(f"  {key}: {value}")
        
        print("Auto modes:")
        for key, value in self.auto_modes.items():
            print(f"  {key}: {value}")
