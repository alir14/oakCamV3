import cv2
import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np
from PIL import Image, ImageTk
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from camera.controller import CameraController
    from utils.file_manager import FileManager


class DisplayManager:
    """Manages camera display and UI updates"""
    
    def __init__(self, notebook: ttk.Notebook):
        self.notebook = notebook
        self.camera_frames: Dict[str, ttk.Label] = {}
        self.camera_info_labels: Dict[str, ttk.Label] = {}
        self.display_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Display settings
        self.display_width = 640
        self.target_fps = 30
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.current_fps = 0.0
    
    def setup_camera_tab(self, camera_name: str):
        """Setup display tab for a camera"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=camera_name)
        
        # Main container for camera content
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info panel at top
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Camera info label
        info_label = ttk.Label(info_frame, text=f"Camera {camera_name} - No Image", 
                              font=("Arial", 10))
        info_label.pack(side=tk.LEFT)
        self.camera_info_labels[camera_name] = info_label
        
        # FPS display
        fps_label = ttk.Label(info_frame, text="FPS: 0.0", font=("Arial", 10))
        fps_label.pack(side=tk.RIGHT)
        
        # Image display area
        image_frame = ttk.Frame(content_frame, relief=tk.SUNKEN, borderwidth=2)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create label for image display
        image_label = ttk.Label(image_frame, text=f"Camera {camera_name}\nWaiting for frames...", 
                               anchor=tk.CENTER, justify=tk.CENTER)
        image_label.pack(expand=True)
        
        self.camera_frames[camera_name] = image_label
        
        # Store fps label reference for updates
        self.camera_frames[f"{camera_name}_fps"] = fps_label
    
    def update_camera_display(self, camera_name: str, image: np.ndarray, 
                            frame_info: Optional[Dict] = None):
        """Update camera display with new image and info"""
        try:
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Calculate display size maintaining aspect ratio
            original_height, original_width = img_rgb.shape[:2]
            display_height = int(original_height * self.display_width / original_width)
            
            # Resize for display
            img_display = cv2.resize(img_rgb, (self.display_width, display_height))
            
            # Convert to PhotoImage
            pil_image = Image.fromarray(img_display)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update display
            if camera_name in self.camera_frames:
                self.camera_frames[camera_name].config(image=photo, text="")
                self.camera_frames[camera_name].image = photo  # Keep reference
                
                # Update info label
                info_text = f"Camera {camera_name} - {original_width}x{original_height}"
                if frame_info:
                    if 'exposure' in frame_info:
                        info_text += f" | Exp: {frame_info['exposure']}μs"
                    if 'sequence' in frame_info:
                        info_text += f" | Frame: {frame_info['sequence']}"
                
                if camera_name in self.camera_info_labels:
                    self.camera_info_labels[camera_name].config(text=info_text)
                
                # Update FPS
                self._update_fps_display(camera_name)
                
        except Exception as e:
            print(f"Display update error for {camera_name}: {e}")
    
    def _update_fps_display(self, camera_name: str):
        """Update FPS display for camera"""
        try:
            current_time = time.time()
            self.frame_count += 1
            
            # Update FPS every second
            if current_time - self.last_fps_update >= 1.0:
                self.current_fps = self.frame_count / (current_time - self.last_fps_update)
                self.frame_count = 0
                self.last_fps_update = current_time
                
                # Update FPS label
                fps_label_key = f"{camera_name}_fps"
                if fps_label_key in self.camera_frames:
                    self.camera_frames[fps_label_key].config(text=f"FPS: {self.current_fps:.1f}")
        except Exception as e:
            print(f"FPS update error: {e}")
    
    def clear_displays(self):
        """Clear all camera displays"""
        for child in self.notebook.tabs():
            self.notebook.forget(child)
        self.camera_frames.clear()
        self.camera_info_labels.clear()
    
    def start_display_loop(self, camera_controller: 'CameraController', 
                          file_manager: 'FileManager'):
        """Start the display update loop"""
        if self.running:
            return
            
        self.running = True
        self.display_thread = threading.Thread(
            target=self._display_loop, 
            args=(camera_controller, file_manager), 
            daemon=True
        )
        self.display_thread.start()
    
    def stop_display_loop(self):
        """Stop the display update loop"""
        self.running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
    
    def _display_loop(self, camera_controller: 'CameraController', 
                     file_manager: 'FileManager'):
        """Main display loop"""
        frame_interval = 1.0 / self.target_fps
        
        while self.running:
            loop_start = time.time()
            
            try:
                for camera_name in camera_controller.get_connected_cameras():
                    frame = camera_controller.get_frame(camera_name)
                    if frame is not None:
                        # Get frame info if available
                        frame_info = {
                            'width': frame.shape[1],
                            'height': frame.shape[0],
                            'channels': frame.shape[2] if len(frame.shape) > 2 else 1
                        }
                        
                        # Update display
                        self.update_camera_display(camera_name, frame, frame_info)
                        
                        # Write to video if recording
                        if file_manager.is_recording():
                            file_manager.write_video_frame(camera_name, frame)
                
                # Maintain target FPS
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Display loop error: {e}")
                time.sleep(0.1)
    
    def set_display_width(self, width: int):
        """Set display width for all cameras"""
        self.display_width = max(320, min(width, 1920))  # Clamp between reasonable values
    
    def get_current_fps(self) -> float:
        """Get current display FPS"""
        return self.current_fps
    
    def take_screenshot(self, camera_name: str) -> Optional[np.ndarray]:
        """Take a screenshot of currently displayed frame"""
        if camera_name in self.camera_frames:
            try:
                # This would require getting the actual frame data
                # For now, we'll return None and handle screenshots differently
                return None
            except Exception as e:
                print(f"Screenshot error: {e}")
        return None
    
    def show_error_on_camera(self, camera_name: str, error_message: str):
        """Show error message on camera display"""
        if camera_name in self.camera_frames:
            self.camera_frames[camera_name].config(
                text=f"Camera {camera_name}\nError: {error_message}",
                image=""
            )
            self.camera_frames[camera_name].image = None
    
    def show_no_signal(self, camera_name: str):
        """Show no signal message on camera display"""
        if camera_name in self.camera_frames:
            self.camera_frames[camera_name].config(
                text=f"Camera {camera_name}\nNo Signal",
                image=""
            )
            self.camera_frames[camera_name].image = None