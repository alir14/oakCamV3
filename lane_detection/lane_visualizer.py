#!/usr/bin/env python3
"""
Lane Detection Visualizer
Draws lane detection results on camera frames
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional


class LaneVisualizer:
    """Visualizes lane detection results on camera frames"""
    
    def __init__(self):
        # Lane colors (BGR format)
        self.lane_colors = [
            (0, 255, 0),    # Green - left lane
            (0, 0, 255),    # Red - right lane
            (255, 0, 0),    # Blue - center lane
            (0, 255, 255),  # Yellow - other lanes
        ]
        
        # Visualization settings
        self.line_thickness = 3
        self.point_radius = 4
        self.show_points = True
        self.show_lines = True
        self.show_filled_area = False
        self.alpha = 0.7  # Transparency for filled area
        
    def draw_lanes(self, frame: np.ndarray, lanes: np.ndarray, 
                   camera_name: str = "CAM_A") -> np.ndarray:
        """Draw lane detection results on frame"""
        if lanes is None or len(lanes) == 0:
            return frame
            
        try:
            # Create a copy for drawing
            result_frame = frame.copy()
            
            # Draw each lane
            for lane_idx, lane_points in enumerate(lanes):
                if len(lane_points) > 0:
                    color = self.lane_colors[lane_idx % len(self.lane_colors)]
                    
                    # Draw lane points
                    if self.show_points:
                        for point in lane_points:
                            cv2.circle(result_frame, point, self.point_radius, color, -1)
                    
                    # Draw lane lines
                    if self.show_lines and len(lane_points) > 1:
                        points_array = np.array(lane_points, dtype=np.int32)
                        cv2.polylines(result_frame, [points_array], False, color, self.line_thickness)
                    
                    # Draw filled area between lanes (if multiple lanes)
                    if self.show_filled_area and len(lanes) >= 2:
                        self._draw_filled_area(result_frame, lanes)
            
            # Add lane count text
            self._add_info_text(result_frame, len(lanes))
            
            return result_frame
            
        except Exception as e:
            print(f"Error drawing lanes: {e}")
            return frame
    
    def _draw_filled_area(self, frame: np.ndarray, lanes: np.ndarray):
        """Draw filled area between detected lanes"""
        try:
            if len(lanes) < 2:
                return
                
            # Get the two main lanes (left and right)
            left_lane = lanes[0] if len(lanes) > 0 else []
            right_lane = lanes[1] if len(lanes) > 1 else []
            
            if len(left_lane) == 0 or len(right_lane) == 0:
                return
            
            # Create polygon points
            polygon_points = []
            
            # Add left lane points (in reverse order for polygon)
            for point in reversed(left_lane):
                polygon_points.append(point)
            
            # Add right lane points
            for point in right_lane:
                polygon_points.append(point)
            
            if len(polygon_points) >= 3:
                # Create overlay for transparency
                overlay = frame.copy()
                
                # Draw filled polygon
                points_array = np.array(polygon_points, dtype=np.int32)
                cv2.fillPoly(overlay, [points_array], (0, 255, 255))  # Cyan color
                
                # Blend with original frame
                cv2.addWeighted(overlay, self.alpha, frame, 1 - self.alpha, 0, frame)
                
        except Exception as e:
            print(f"Error drawing filled area: {e}")
    
    def _add_info_text(self, frame: np.ndarray, lane_count: int):
        """Add information text to frame"""
        try:
            text = f"Lanes: {lane_count}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            color = (255, 255, 255)  # White
            
            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Position text in top-left corner
            x = 10
            y = text_height + 10
            
            # Draw background rectangle
            cv2.rectangle(frame, (x - 5, y - text_height - 5), 
                         (x + text_width + 5, y + baseline + 5), (0, 0, 0), -1)
            
            # Draw text
            cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)
            
        except Exception as e:
            print(f"Error adding info text: {e}")
    
    def set_visualization_options(self, show_points: bool = True, 
                                 show_lines: bool = True, 
                                 show_filled_area: bool = False):
        """Set visualization options"""
        self.show_points = show_points
        self.show_lines = show_lines
        self.show_filled_area = show_filled_area
    
    def set_line_thickness(self, thickness: int):
        """Set line thickness for lane visualization"""
        self.line_thickness = max(1, thickness)
    
    def set_point_radius(self, radius: int):
        """Set point radius for lane visualization"""
        self.point_radius = max(1, radius)
    
    def set_transparency(self, alpha: float):
        """Set transparency for filled area"""
        self.alpha = max(0.0, min(1.0, alpha))
    
    def set_lane_colors(self, colors: List[Tuple[int, int, int]]):
        """Set custom lane colors (BGR format)"""
        if colors and len(colors) > 0:
            self.lane_colors = colors
