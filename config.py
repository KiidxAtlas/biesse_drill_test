"""
Configuration file for the drill CIX generator.
This file contains all the settings and parameters for generating drill test programs.
"""

import os
from typing import Dict, List


class DrillTestConfig:
    """Configuration class for drill test generation."""

    #TODO
    depth_limits_by_diameter: Dict[float, float]

    def __init__(self):
        # Default drill test parameters
        self.start_x = 0.0
        self.start_y = 0.0
        self.x_spacing = 32.0
        self.y_spacing = 50.0
        self.depth = 19
        self.panel_thickness = 19.0  # LPZ in CIX (mm)
        self.output_file = "R2_Drill_Test.cix"

        # Tool configuration file path
        self.tool_xml_file = "r2_spindle_tooling.xml"  # Default to R1 tools

        # Test parameters
        self.test_all_tools = False  # If True, test all available tools
        self.custom_tool_config = None  # Custom diameter to spindle mapping

        # Safety parameters
        self.max_holes_per_row = 99
        self.min_spacing = 20.0  # Minimum spacing between holes
        self.max_depth = 20  # Maximum drill depth

        # Program metadata
        self.program_name = "DrillTest"
        self.units = "MM"
        self.author = "CIX Generator"
        self.description = "Automated drill test program"

        # Panel size settings
        self.auto_size_panel = True  # Automatically calculate panel size
        self.panel_margin = 5.0  # Margin around drill test (mm)

        # Machining parameters
        self.engraving_tool_name = "V45D22MM"  # Tool name for engraving operations
        self.engraving_depth = 0.5  # Engraving depth (mm)
        self.drill_speed = 0  # RPM for drilling operations
        self.engraving_speed = 0  # RPM for engraving operations
        self.feed_rate = 0  # Feed rate (mm/min)

        # File naming
        self.auto_timestamp = True  # Add timestamp to filename
        self.timestamp_format = "%m_%d_%Y"  # MM_DD_YYYY format

        # Per-diameter depth limits: diameter(mm) -> max depth(mm)
        # Default rule: 2mm diameter drills can only go 2mm deep
        self.depth_limits_by_diameter = {2.0: 2.0}


    def set_tool_xml_file(self, filename: str) -> None:
        """Set the XML file to read tool information from."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Tool XML file not found: {filename}")
        self.tool_xml_file = filename

    def set_spacing(self, x_spacing: float, y_spacing: float) -> None:
        """Set the spacing between holes."""
        if x_spacing < self.min_spacing or y_spacing < self.min_spacing:
            raise ValueError(f"Spacing must be at least {self.min_spacing}mm")
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing

    def set_start_position(self, x: float, y: float) -> None:
        """Set the starting position for the drill test."""
        self.start_x = x
        self.start_y = y

    def set_drill_depth(self, depth: float) -> None:
        """Set the drill depth with safety check."""
        if depth > self.max_depth:
            raise ValueError(f"Drill depth cannot exceed {self.max_depth}mm")
        if depth <= 0:
            raise ValueError("Drill depth must be positive")
        self.depth = depth

    def set_max_depth_for_diameter(self, diameter: float, max_depth: float) -> None:
        """
        Set a maximum drill depth for a specific tool diameter (in mm).

        The effective drill depth used will be min(global depth, per-diameter max).
        """
        if diameter <= 0:
            raise ValueError("Diameter must be positive")
        if max_depth <= 0:
            raise ValueError("Max depth must be positive")
        if max_depth > self.max_depth:
            raise ValueError(
                f"Per-diameter max depth cannot exceed global max depth {self.max_depth}mm"
            )
        self.depth_limits_by_diameter[float(diameter)] = float(max_depth)

    def clear_depth_limit_for_diameter(self, diameter: float) -> None:
        """Remove a per-diameter depth limit if present."""
        self.depth_limits_by_diameter.pop(float(diameter), None)

    def get_effective_drill_depth(self, diameter: float) -> float:
        """
        Get the effective drill depth for a given diameter, honoring per-diameter limits.

        Returns the minimum of the global depth and the configured limit for the
        closest matching diameter key (within a small tolerance), if any.
        """
        # Exact match first
        limit = self.depth_limits_by_diameter.get(float(diameter))
        if limit is not None:
            return min(self.depth, limit)

        # Fuzzy match within 0.1mm to be robust to parsing
        for d_key, d_limit in self.depth_limits_by_diameter.items():
            if abs(d_key - float(diameter)) <= 0.1:
                return min(self.depth, d_limit)

        return self.depth

    def set_panel_thickness(self, thickness: float) -> None:
        """Set the panel thickness (LPZ) in mm."""
        if thickness <= 0:
            raise ValueError("Panel thickness must be positive")
        if thickness > 1000:
            # Guard against obviously invalid values
            raise ValueError("Panel thickness is unreasonably large")
        self.panel_thickness = float(thickness)

    def set_custom_tools(self, tool_config: Dict[float, List[int]]) -> None:
        """
        Set custom tool configuration.

        Args:
            tool_config: Dictionary mapping diameters to lists of spindle IDs
                        e.g. {5.0: [1, 2, 3], 8.0: [4, 5, 6]}
        """
        self.custom_tool_config = tool_config
        self.test_all_tools = False

    def enable_all_tools_test(self) -> None:
        """Enable testing of all available tools from the XML file."""
        self.test_all_tools = True
        self.custom_tool_config = None

    def set_panel_sizing(self, auto_size: bool = True, margin: float = 5.0) -> None:
        """
        Configure panel sizing options.

        Args:
            auto_size: If True, automatically calculate panel size from layout
            margin: Margin to add around the drill test layout (mm)
        """
        self.auto_size_panel = auto_size
        self.panel_margin = margin

    def set_manual_panel_size(self, width: float, height: float) -> None:
        """
        Set manual panel size (disables auto-sizing).

        Args:
            width: Panel width (LPX) in mm
            height: Panel height (LPY) in mm
        """
        self.auto_size_panel = False
        self.manual_panel_width = width
        self.manual_panel_height = height

    def set_machining_parameters(
        self, drill_speed=None, engraving_speed=None, feed_rate=None
    ) -> None:
        """
        Set machining speed parameters.

        Args:
            drill_speed: RPM for drilling operations
            engraving_speed: RPM for engraving operations
            feed_rate: Feed rate in mm/min
        """
        if drill_speed is not None:
            if drill_speed < 1000 or drill_speed > 24000:
                raise ValueError("Drill speed must be between 1000-24000 RPM")
            self.drill_speed = drill_speed

        if engraving_speed is not None:
            if engraving_speed < 1000 or engraving_speed > 24000:
                raise ValueError("Engraving speed must be between 1000-24000 RPM")
            self.engraving_speed = engraving_speed

        if feed_rate is not None:
            if feed_rate < 100 or feed_rate > 5000:
                raise ValueError("Feed rate must be between 100-5000 mm/min")
            self.feed_rate = feed_rate

    def set_engraving_tool(self, tool_name: str, depth=None) -> None:
        """
        Set the engraving tool and depth.

        Args:
            tool_name: Tool name for engraving operations (e.g., "v45d6mm", "v90d3mm")
            depth: Engraving depth in mm (optional)
        """
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("Tool name must be a non-empty string")
        self.engraving_tool_name = tool_name.strip()

        if depth is not None:
            if depth < 0.1 or depth > 2.0:
                raise ValueError("Engraving depth must be between 0.1-2.0 mm")
            self.engraving_depth = depth

    def set_file_naming(
        self, auto_timestamp: bool = True, timestamp_format: str = "%m_%d_%Y"
    ) -> None:
        """
        Configure file naming options.

        Args:
            auto_timestamp: Whether to add timestamp to filename
            timestamp_format: Format string for timestamp (default: MM_DD_YYYY)
        """
        self.auto_timestamp = auto_timestamp
        self.timestamp_format = timestamp_format

    def get_output_filename(self) -> str:
        """
        Get the final output filename with timestamp if enabled.

        Returns:
            Final filename with or without timestamp
        """
        if not self.auto_timestamp:
            return self.output_file

        import datetime

        timestamp = datetime.datetime.now().strftime(self.timestamp_format)

        # Insert timestamp before file extension
        if "." in self.output_file:
            name, ext = self.output_file.rsplit(".", 1)
            return f"{name}_{timestamp}.{ext}"
        else:
            return f"{self.output_file}_{timestamp}"

    def validate_config(self) -> List[str]:
        """
        Validate the current configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not os.path.exists(self.tool_xml_file):
            errors.append(f"Tool XML file not found: {self.tool_xml_file}")

        if self.x_spacing < self.min_spacing:
            errors.append(f"X spacing too small: {self.x_spacing} < {self.min_spacing}")

        if self.y_spacing < self.min_spacing:
            errors.append(f"Y spacing too small: {self.y_spacing} < {self.min_spacing}")

        if self.depth <= 0 or self.depth > self.max_depth:
            errors.append(
                f"Invalid drill depth: {self.depth} (must be 0 < depth <= {self.max_depth})"
            )

        if self.custom_tool_config:
            for diameter, spindles in self.custom_tool_config.items():
                if diameter <= 0:
                    errors.append(f"Invalid diameter: {diameter}")
                if not spindles:
                    errors.append(f"No spindles specified for diameter {diameter}")
                if len(spindles) > self.max_holes_per_row:
                    errors.append(
                        f"Too many spindles for diameter {diameter}: {len(spindles)} > {self.max_holes_per_row}"
                    )

        if self.panel_thickness <= 0:
            errors.append("Panel thickness must be positive")

        # Validate per-diameter depth limits
        for d_key, d_lim in self.depth_limits_by_diameter.items():
            if d_key <= 0:
                errors.append(f"Invalid diameter for depth limit: {d_key}")
            if d_lim <= 0:
                errors.append(f"Invalid max depth for diameter {d_key}: {d_lim}")
            if d_lim > self.max_depth:
                errors.append(
                    f"Max depth for diameter {d_key} exceeds global max ({d_lim} > {self.max_depth})"
                )

        return errors

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for serialization."""
        return {
            "start_x": self.start_x,
            "start_y": self.start_y,
            "x_spacing": self.x_spacing,
            "y_spacing": self.y_spacing,
            "depth": self.depth,
            "panel_thickness": self.panel_thickness,
            "output_file": self.output_file,
            "tool_xml_file": self.tool_xml_file,
            "test_all_tools": self.test_all_tools,
            "custom_tool_config": self.custom_tool_config,
            "program_name": self.program_name,
            "units": self.units,
            "author": self.author,
            "description": self.description,
            "depth_limits_by_diameter": self.depth_limits_by_diameter,
        }

    def __str__(self) -> str:
        """String representation of the configuration."""
        panel_info = (
            "Auto-calculated"
            if self.auto_size_panel
            else f"Manual ({getattr(self, 'manual_panel_width', 438.0)}x{getattr(self, 'manual_panel_height', 640.0)})"
        )
        return f"""Drill Test Configuration:
  Tool XML File: {self.tool_xml_file}
  Start Position: ({self.start_x}, {self.start_y})
  Spacing: X={self.x_spacing}, Y={self.y_spacing}
  Drill Depth: {self.depth}mm
    Panel Thickness (LPZ): {self.panel_thickness}mm
  Output File: {self.get_output_filename()}
  Test All Tools: {self.test_all_tools}
  Custom Tools: {self.custom_tool_config is not None}
  Panel Size: {panel_info} (Margin: {self.panel_margin}mm)
  Machining: Drill={self.drill_speed}RPM, Engrave={self.engraving_speed}RPM, Feed={self.feed_rate}mm/min
  Engraving: Tool={self.engraving_tool_name}, Depth={self.engraving_depth}mm
  Timestamp: {self.auto_timestamp}
"""


# Default configuration instance
default_config = DrillTestConfig()

# Example configurations for different scenarios
example_configs = {
    "small_holes": {
        "description": "Test small diameter holes (3-6mm)",
        "custom_tools": {
            3.0: [6, 16, 27],
            4.0: [4, 24, 27],
            5.0: [7, 8, 9, 13, 14, 16, 23, 25],
            6.0: [20],
        },
        "spacing": (25.0, 40.0),
        "depth": 12.0,
    },
    "medium_holes": {
        "description": "Test medium diameter holes (8-12mm)",
        "custom_tools": {8.0: [10, 12, 15, 17], 10.0: [1, 3], 12.0: [2]},
        "spacing": (35.0, 50.0),
        "depth": 15.0,
    },
    "large_holes": {
        "description": "Test large diameter holes (15-35mm)",
        "custom_tools": {15.0: [5], 20.0: [26], 35.0: [11]},
        "spacing": (50.0, 70.0),
        "depth": 18.0,
    },
    "all_available": {
        "description": "Test all available tools from XML",
        "test_all_tools": True,
    "spacing": (40.0, 60.0),
    "depth": 19.0,
    },
}


def create_config_from_example(example_name: str) -> DrillTestConfig:
    """
    Create a configuration from one of the predefined examples.

    Args:
        example_name: Name of the example configuration

    Returns:
        Configured DrillTestConfig instance
    """
    if example_name not in example_configs:
        raise ValueError(
            f"Unknown example config: {example_name}. Available: {list(example_configs.keys())}"
        )

    config = DrillTestConfig()
    example = example_configs[example_name]

    if "custom_tools" in example:
        config.set_custom_tools(example["custom_tools"])

    if "test_all_tools" in example and example["test_all_tools"]:
        config.enable_all_tools_test()

    if "spacing" in example:
        config.set_spacing(*example["spacing"])

    if "depth" in example:
        config.set_drill_depth(example["depth"])

    return config
