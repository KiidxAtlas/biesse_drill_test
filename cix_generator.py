"""
CIX Generator for Biesse Rover Drill Tests
Generates drill test programs by reading tool XML files and configuration settings.
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import glob

from config import DrillTestConfig


class Tool:
    """Represents a drill tool with its properties."""

    def __init__(self, spindle_id: int, diameter: float, description: str = ""):
        self.spindle_id = spindle_id
        self.diameter = diameter
        self.description = description

    def __str__(self):
        return f"Tool(ID={self.spindle_id}, D={self.diameter}mm, {self.description})"


class ToolManager:
    """Manages tool information from XML files."""

    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.tools: Dict[int, Tool] = {}
        self.load_tools()

    def load_tools(self) -> None:
        """Load tools from XML file."""
        if not os.path.exists(self.xml_file):
            raise FileNotFoundError(f"XML file not found: {self.xml_file}")

        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            # Handle Biesse XML format with Spindle elements
            spindle_elements = root.findall(".//Spindle")

            for spindle_elem in spindle_elements:
                # Extract spindle name (e.g., "T1", "T2", etc.)
                name = spindle_elem.get("Name", "")
                child = spindle_elem.get("Child", "")

                if name and child:
                    # Extract spindle ID from name (T1 -> 1, T10 -> 10, etc.)
                    spindle_id = self._extract_spindle_id(name)

                    # Extract diameter from child (e.g., "D10MM70" -> 10.0)
                    diameter = self._extract_diameter(child)

                    if spindle_id is not None and diameter is not None:
                        description = f"{child} ({name})"
                        self.tools[spindle_id] = Tool(spindle_id, diameter, description)

            print(f"✅ Loaded {len(self.tools)} tools from {self.xml_file}")

        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file {self.xml_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading tools from {self.xml_file}: {e}")

    def _extract_spindle_id(self, name: str) -> Optional[int]:
        """Extract numeric spindle ID from name like 'T1', 'T10', 'TP1'."""
        if not name:
            return None

        # Remove non-numeric characters and extract the number
        import re

        match = re.search(r"(\d+)", name)
        if match:
            return int(match.group(1))
        return None

    def _extract_diameter(self, child: str) -> Optional[float]:
        """Extract diameter from child string like 'D10MM70', 'D5MM70', 'D1_4IN70'."""
        if not child:
            return None

        import re

        # Handle formats like D10MM70, D5MM70
        mm_match = re.search(r"D(\d+(?:\.\d+)?)MM", child)
        if mm_match:
            return float(mm_match.group(1))

        # Handle formats like D1_4IN70 (1/4 inch = 6.35mm)
        inch_match = re.search(r"D(\d+)_(\d+)IN", child)
        if inch_match:
            numerator = float(inch_match.group(1))
            denominator = float(inch_match.group(2))
            inches = numerator / denominator
            return inches * 25.4  # Convert to mm

        # Handle decimal formats like D6.35MM70
        decimal_match = re.search(r"D(\d+\.\d+)MM", child)
        if decimal_match:
            return float(decimal_match.group(1))

        return None

    def get_tool(self, spindle_id: int) -> Optional[Tool]:
        """Get tool by spindle ID."""
        return self.tools.get(spindle_id)

    def get_tools_by_diameter(
        self, diameter: float, tolerance: float = 0.1
    ) -> List[Tool]:
        """Get all tools with approximately the specified diameter."""
        return [
            tool
            for tool in self.tools.values()
            if abs(tool.diameter - diameter) <= tolerance
        ]

    def get_all_tools(self) -> List[Tool]:
        """Get all available tools."""
        return list(self.tools.values())

    def get_diameter_groups(self) -> Dict[float, List[int]]:
        """Group tools by diameter, returning spindle IDs for each diameter."""
        diameter_groups = {}
        for tool in self.tools.values():
            if tool.diameter not in diameter_groups:
                diameter_groups[tool.diameter] = []
            diameter_groups[tool.diameter].append(tool.spindle_id)

        # Sort spindle IDs within each group
        for diameter in diameter_groups:
            diameter_groups[diameter].sort()

        return diameter_groups


class CIXGenerator:
    """Generates CIX drill test programs."""

    def __init__(self, config: DrillTestConfig):
        self.config = config
        self.tool_manager = ToolManager(config.tool_xml_file)

    def generate_cix(self) -> str:
        """
        Generate a CIX drill test program.

        Returns:
            The generated CIX content as a string
        """
        # Validate configuration
        errors = self.config.validate_config()
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")

        # Determine which tools to use
        if self.config.test_all_tools:
            tool_config = self.tool_manager.get_diameter_groups()
        elif self.config.custom_tool_config:
            tool_config = self.config.custom_tool_config
        else:
            raise ValueError("No tool configuration specified")

        # Generate CIX content
        cix_content = self._generate_cix_content(tool_config)

        # Write to file
        output_filename = self.config.get_output_filename()
        with open(output_filename, "w") as f:
            f.write(cix_content)

        print(f"✅ CIX drill test generated: {output_filename}")
        return cix_content

    def _calculate_layout_bounds(self, tool_config: Dict[float, List[int]]) -> tuple:
        """
        Calculate the bounds of the drill test layout accounting for drill radii and text.

        Returns:
            tuple: (min_x, min_y, max_x, max_y) of the layout including text and drill extents
        """
        sorted_diameters = sorted(tool_config.keys())

        # Track actual drill extents (center ± radius)
        drill_positions = []
        current_y = 20.0  # Start Y like reference
        max_x_center = 20.0  # Track furthest drill center

        # Calculate all drill positions and track extents
        for diameter in sorted_diameters:
            spindles = tool_config[diameter]
            current_x = 20.0  # Start X like reference

            for spindle_id in spindles:
                drill_positions.append(
                    {
                        "x": current_x,
                        "y": current_y,
                        "diameter": diameter,
                        "radius": diameter / 2.0,
                    }
                )
                current_x += 32.0  # 32mm spacing like reference
                max_x_center = max(max_x_center, current_x - 32.0)

            current_y += 50.0  # Move to next row

        # Calculate actual bounds including drill radii
        if not drill_positions:
            return (20.0, 20.0, 50.0, 50.0)  # Fallback for empty layout

        # Find minimum and maximum extents including drill bit radii
        min_x = min(pos["x"] - pos["radius"] for pos in drill_positions)
        min_y = min(pos["y"] - pos["radius"] for pos in drill_positions)
        max_x_drill = max(pos["x"] + pos["radius"] for pos in drill_positions)
        max_y_drill = max(pos["y"] + pos["radius"] for pos in drill_positions)

        # Calculate text position (40mm beyond the last drill center, like current logic)
        text_x_position = max_x_center + 40.0

        # Text extends about 50mm to the right (more conservative estimate)
        # Text height is about 6mm (3mm font height + margins)
        text_max_x = text_x_position + 50.0
        text_max_y = max_y_drill  # Text aligns with drill rows

        # Final bounds include both drill extents and text
        # Make sure bounds start from 0,0 by adjusting negative extents
        final_min_x = min(0.0, min_x)
        final_min_y = min(0.0, min_y)
        final_max_x = max(max_x_drill, text_max_x)
        final_max_y = max_y_drill

        return (final_min_x, final_min_y, final_max_x, final_max_y)

    def _generate_cix_content(self, tool_config: Dict[float, List[int]]) -> str:
        """Generate CIX content (CID3) using current config and tools."""
        lines: List[str] = []

        # Panel size
        if self.config.auto_size_panel:
            min_x, min_y, max_x, max_y = self._calculate_layout_bounds(tool_config)
            panel_width = max_x - min_x + (2 * self.config.panel_margin)
            panel_height = max_y - min_y + (2 * self.config.panel_margin)
        else:
            panel_width = getattr(self.config, "manual_panel_width", 438.0)
            panel_height = getattr(self.config, "manual_panel_height", 640.0)

        # Header
        lines.append("BEGIN ID CID3")
        lines.append("\tREL= 5.0")
        lines.append("END ID")
        lines.append(" ")

        # MAINDATA with panel thickness (LPZ)
        lines.append("BEGIN MAINDATA")
        lines.append(f"\tLPX={panel_width}")
        lines.append(f"\tLPY={panel_height}")
        lines.append(f"\tLPZ={self.config.panel_thickness}")
        lines.append('\tORLST="1"')
        lines.append("\tSIMMETRY=1")
        lines.append("\tTLCHK=0")
        lines.append('\tTOOLING=""')
        lines.append('\tCUSTSTR=$B$KBsExportToNcRoverNET.XncExtraPanelData$V""')
        lines.append("\tFCN=1.000000")
        lines.append("\tXCUT=0")
        lines.append("\tYCUT=0")
        lines.append("\tJIGTH=0")
        lines.append("\tCKOP=0")
        lines.append("\tUNIQUE=0")
        lines.append('\tMATERIAL="wood"')
        lines.append('\tPUTLST=""')
        lines.append("\tOPPWKRS=0")
        lines.append("\tUNICLAMP=0")
        lines.append("\tCHKCOLL=0")
        lines.append("\tWTPIANI=0")
        lines.append("\tCOLLTOOL=0")
        lines.append("\tCALCEDTH=0")
        lines.append("\tENABLELABEL=0")
        lines.append("\tLOCKWASTE=0")
        lines.append("\tLOADEDGEOPT=0")
        lines.append("\tITLTYPE=0")
        lines.append("\tRUNPAV=0")
        lines.append("\tFLIPEND=0")
        lines.append("END MAINDATA")
        lines.append("")

        # Layout drill positions
        sorted_diameters = sorted(tool_config.keys())
        drill_positions: List[Dict] = []
        current_y = 20.0
        max_x_extent = 20.0
        for diameter in sorted_diameters:
            spindles = tool_config[diameter]
            current_x = 20.0
            for spindle_id in spindles:
                drill_positions.append({
                    "diameter": diameter,
                    "spindle_id": spindle_id,
                    "x": current_x,
                    "y": current_y,
                })
                current_x += 32.0
                max_x_extent = max(max_x_extent, current_x - 32.0)
            current_y += 50.0

        # Engrave labels per diameter row
        text_x_position = max_x_extent + 40.0
        text_id_counter = 1001
        routg_id_counter = 1001
        for diameter in sorted_diameters:
            tool_count = len(tool_config[diameter])
            label_text = f"{diameter}mm - {tool_count}"
            first_drill = next(pos for pos in drill_positions if pos["diameter"] == diameter)
            text_x = text_x_position
            text_y = first_drill["y"]

            lines.append("BEGIN MACRO")
            lines.append("\tNAME=GEOTEXT")
            lines.append('\tPARAM,NAME=LAY,VALUE="Layer 0"')
            lines.append(f'\tPARAM,NAME=ID,VALUE="G{text_id_counter}.{text_id_counter}"')
            lines.append("\tPARAM,NAME=SIDE,VALUE=0")
            lines.append('\tPARAM,NAME=CRN,VALUE="2"')
            lines.append("\tPARAM,NAME=RTY,VALUE=2")
            lines.append("\tPARAM,NAME=NRP,VALUE=0")
            lines.append("\tPARAM,NAME=DX,VALUE=0")
            lines.append("\tPARAM,NAME=DY,VALUE=0")
            lines.append(f'\tPARAM,NAME=TXT,VALUE="{label_text}"')
            lines.append(f"\tPARAM,NAME=X,VALUE={text_x}")
            lines.append(f"\tPARAM,NAME=Y,VALUE={text_y}")
            lines.append("\tPARAM,NAME=Z,VALUE=0")
            lines.append("\tPARAM,NAME=ALN,VALUE=1")
            lines.append("\tPARAM,NAME=ANG,VALUE=0")
            lines.append("\tPARAM,NAME=VRS,VALUE=0")
            lines.append("\tPARAM,NAME=ACC,VALUE=0.1")
            lines.append("\tPARAM,NAME=CIR,VALUE=0")
            lines.append("\tPARAM,NAME=RDS,VALUE=0")
            lines.append("\tPARAM,NAME=PST,VALUE=0")
            lines.append('\tPARAM,NAME=FNT,VALUE="Arial"')
            lines.append("\tPARAM,NAME=SZE,VALUE=8")
            lines.append("\tPARAM,NAME=BOL,VALUE=0")
            lines.append("\tPARAM,NAME=ITL,VALUE=0")
            lines.append("\tPARAM,NAME=UDL,VALUE=0")
            lines.append("\tPARAM,NAME=STR,VALUE=0")
            lines.append("\tPARAM,NAME=WGH,VALUE=1")
            lines.append("\tPARAM,NAME=CHS,VALUE=0")
            lines.append("END MACRO")
            lines.append("")

            lines.append("BEGIN MACRO")
            lines.append("\tNAME=ROUTG")
            lines.append('\tPARAM,NAME=LAY,VALUE="Layer 0"')
            lines.append(f'\tPARAM,NAME=ID,VALUE="RG{routg_id_counter}.{routg_id_counter}"')
            lines.append(f'\tPARAM,NAME=GID,VALUE="G{text_id_counter}.{text_id_counter}"')
            lines.append('\tPARAM,NAME=SIL,VALUE=""')
            lines.append("\tPARAM,NAME=Z,VALUE=0")
            # Use configured engraving depth
            lines.append(f"\tPARAM,NAME=DP,VALUE={self.config.engraving_depth}")
            lines.append("\tPARAM,NAME=DIA,VALUE=0")
            lines.append("\tPARAM,NAME=THR,VALUE=0")
            lines.append("\tPARAM,NAME=RV,VALUE=0")
            lines.append("\tPARAM,NAME=CRC,VALUE=0")
            lines.append("\tPARAM,NAME=CKA,VALUE=3")
            lines.append("\tPARAM,NAME=AZ,VALUE=0")
            lines.append("\tPARAM,NAME=AR,VALUE=0")
            lines.append("\tPARAM,NAME=OPT,VALUE=1")
            lines.append("\tPARAM,NAME=RSP,VALUE=0")
            lines.append("\tPARAM,NAME=IOS,VALUE=0")
            lines.append("\tPARAM,NAME=WSP,VALUE=0")
            lines.append("\tPARAM,NAME=DSP,VALUE=0")
            lines.append("\tPARAM,NAME=IMS,VALUE=0")
            lines.append("\tPARAM,NAME=VTR,VALUE=1")
            lines.append("\tPARAM,NAME=DVR,VALUE=0")
            lines.append("\tPARAM,NAME=INCSTP,VALUE=0")
            lines.append("\tPARAM,NAME=OTR,VALUE=1")
            lines.append("\tPARAM,NAME=SVR,VALUE=0")
            lines.append("\tPARAM,NAME=COF,VALUE=0")
            lines.append("\tPARAM,NAME=DOF,VALUE=0")
            lines.append("\tPARAM,NAME=TIN,VALUE=0")
            lines.append("\tPARAM,NAME=CIN,VALUE=1")
            lines.append("\tPARAM,NAME=AIN,VALUE=90")
            lines.append("\tPARAM,NAME=GIN,VALUE=0")
            lines.append("\tPARAM,NAME=TLI,VALUE=0")
            lines.append("\tPARAM,NAME=TQI,VALUE=0")
            lines.append("\tPARAM,NAME=TBI,VALUE=0")
            lines.append("\tPARAM,NAME=DIN,VALUE=0")
            lines.append("\tPARAM,NAME=TOU,VALUE=0")
            lines.append("\tPARAM,NAME=COU,VALUE=1")
            lines.append("\tPARAM,NAME=AOU,VALUE=90")
            lines.append("\tPARAM,NAME=GOU,VALUE=0")
            lines.append("\tPARAM,NAME=TBO,VALUE=0")
            lines.append("\tPARAM,NAME=TLO,VALUE=0")
            lines.append("\tPARAM,NAME=TQO,VALUE=0")
            lines.append("\tPARAM,NAME=DOU,VALUE=0")
            lines.append("\tPARAM,NAME=PRP,VALUE=100")
            lines.append("\tPARAM,NAME=SDS,VALUE=0")
            lines.append("\tPARAM,NAME=SDSF,VALUE=2000")
            lines.append("\tPARAM,NAME=UDT,VALUE=0")
            lines.append('\tPARAM,NAME=TDT,VALUE=""')
            lines.append("\tPARAM,NAME=DDT,VALUE=5")
            lines.append("\tPARAM,NAME=SDT,VALUE=0")
            lines.append("\tPARAM,NAME=IDT,VALUE=20")
            lines.append("\tPARAM,NAME=FDT,VALUE=80")
            lines.append("\tPARAM,NAME=RDT,VALUE=60")
            lines.append("\tPARAM,NAME=CRR,VALUE=0")
            lines.append("\tPARAM,NAME=GIP,VALUE=1")
            lines.append("\tPARAM,NAME=OVM,VALUE=0")
            lines.append("\tPARAM,NAME=SWI,VALUE=0")
            lines.append("\tPARAM,NAME=BLW,VALUE=0")
            lines.append("\tPARAM,NAME=TOS,VALUE=1")
            lines.append(f'\tPARAM,NAME=TNM,VALUE="{self.config.engraving_tool_name.upper()}"')
            lines.append("\tPARAM,NAME=TTP,VALUE=0")
            lines.append('\tPARAM,NAME=SPI,VALUE=""')
            lines.append("\tPARAM,NAME=BFC,VALUE=0")
            lines.append("\tPARAM,NAME=SHT,VALUE=0")
            lines.append("\tPARAM,NAME=SHP,VALUE=0")
            lines.append("\tPARAM,NAME=SHD,VALUE=0")
            lines.append("\tPARAM,NAME=PRS,VALUE=0")
            lines.append("\tPARAM,NAME=NEBS,VALUE=0")
            lines.append("\tPARAM,NAME=ETB,VALUE=0")
            lines.append("\tPARAM,NAME=FXD,VALUE=0")
            lines.append("\tPARAM,NAME=FXDA,VALUE=0")
            lines.append("\tPARAM,NAME=KDT,VALUE=0")
            lines.append("\tPARAM,NAME=EML,VALUE=0")
            lines.append("\tPARAM,NAME=CKT,VALUE=0")
            lines.append("\tPARAM,NAME=ETG,VALUE=0")
            lines.append("\tPARAM,NAME=ETGT,VALUE=0.1")
            lines.append("\tPARAM,NAME=AJT,VALUE=0")
            lines.append("\tPARAM,NAME=ION,VALUE=0")
            lines.append("\tPARAM,NAME=LUBMNZ,VALUE=0")
            lines.append("\tPARAM,NAME=LPR,VALUE=1")
            lines.append("\tPARAM,NAME=LNG,VALUE=0")
            lines.append("\tPARAM,NAME=ZS,VALUE=0")
            lines.append("\tPARAM,NAME=ZE,VALUE=0")
            lines.append("\tPARAM,NAME=RDIN,VALUE=0")
            lines.append("\tPARAM,NAME=COPRES,VALUE=0")
            lines.append("\tPARAM,NAME=CRT,VALUE=0")
            lines.append("END MACRO")
            lines.append("")

            lines.append("BEGIN MACRO")
            lines.append("\tNAME=ENDPATH")
            lines.append("END MACRO")
            lines.append("")

            text_id_counter += 1
            routg_id_counter += 1

        # Drill operations for each planned hole
        drill_id_counter = 2001
        for drill_pos in drill_positions:
            # Clamp depth based on diameter-specific limits (e.g., 2mm tool -> max 2mm)
            effective_dp = self.config.get_effective_drill_depth(drill_pos['diameter'])
            lines.append("BEGIN MACRO")
            lines.append("\tNAME=BG")
            lines.append('\tPARAM,NAME=LAY,VALUE="BG"')
            lines.append(f'\tPARAM,NAME=ID,VALUE="T{drill_pos['spindle_id']}"')
            lines.append("\tPARAM,NAME=SIDE,VALUE=0")
            lines.append('\tPARAM,NAME=CRN,VALUE="2"')
            lines.append(f"\tPARAM,NAME=X,VALUE={drill_pos['x']}")
            lines.append(f"\tPARAM,NAME=Y,VALUE={drill_pos['y']}")
            lines.append("\tPARAM,NAME=Z,VALUE=0")
            lines.append("\tPARAM,NAME=AP,VALUE=0")
            lines.append("\tPARAM,NAME=MD,VALUE=0")
            lines.append(f"\tPARAM,NAME=DP,VALUE={effective_dp}")
            lines.append('\tPARAM,NAME=TNM,VALUE=""')
            lines.append(f"\tPARAM,NAME=DIA,VALUE={drill_pos['diameter']}")
            lines.append("\tPARAM,NAME=THR,VALUE=0")
            lines.append("\tPARAM,NAME=CKA,VALUE=3")
            lines.append("\tPARAM,NAME=AZ,VALUE=0")
            lines.append("\tPARAM,NAME=AR,VALUE=0")
            lines.append("\tPARAM,NAME=RTY,VALUE=5")
            lines.append(f"\tPARAM,NAME=RSP,VALUE={self.config.drill_speed}")
            lines.append("\tPARAM,NAME=IOS,VALUE=0")
            lines.append("\tPARAM,NAME=WSP,VALUE=0")
            lines.append("\tPARAM,NAME=DDS,VALUE=0")
            lines.append("\tPARAM,NAME=DSP,VALUE=0")
            lines.append("\tPARAM,NAME=RMD,VALUE=1")
            lines.append("\tPARAM,NAME=DQT,VALUE=0")
            lines.append("\tPARAM,NAME=ERDW,VALUE=0")
            lines.append("\tPARAM,NAME=DFW,VALUE=0")
            lines.append("\tPARAM,NAME=TOS,VALUE=1")
            lines.append("\tPARAM,NAME=VTR,VALUE=0")
            lines.append("\tPARAM,NAME=TTP,VALUE=0")
            # SPI expects the spindle name, e.g., 't7' instead of just '7'
            lines.append(f"\tPARAM,NAME=SPI,VALUE=\"t{drill_pos['spindle_id']}\"")
            lines.append("\tPARAM,NAME=BFC,VALUE=0")
            lines.append("\tPARAM,NAME=PRS,VALUE=0")
            lines.append("\tPARAM,NAME=SHT,VALUE=0")
            lines.append("\tPARAM,NAME=SHP,VALUE=0")
            lines.append("\tPARAM,NAME=SHD,VALUE=0")
            lines.append("\tPARAM,NAME=COPRES,VALUE=0")
            lines.append("\tPARAM,NAME=AJT,VALUE=0")
            lines.append("\tPARAM,NAME=ION,VALUE=0")
            lines.append("END MACRO")
            lines.append("")

            drill_id_counter += 1

        return "\n".join(lines)

    def print_tool_summary(self) -> None:
        """Print a summary of available tools."""
        print(f"\n📋 Tool Summary from {self.config.tool_xml_file}:")
        print("-" * 50)

        diameter_groups = self.tool_manager.get_diameter_groups()
        for diameter in sorted(diameter_groups.keys()):
            spindles = diameter_groups[diameter]
            print(f"  {diameter:5.1f}mm: Spindles {spindles}")

        print(f"\nTotal tools: {len(self.tool_manager.tools)}")
        print(f"Total diameters: {len(diameter_groups)}")

    def validate_spindles(self, tool_config: Dict[float, List[int]]) -> List[str]:
        """Validate that all specified spindles exist in the XML."""
        errors = []
        for diameter, spindles in tool_config.items():
            for spindle_id in spindles:
                tool = self.tool_manager.get_tool(spindle_id)
                if not tool:
                    errors.append(
                        f"Spindle {spindle_id} not found in {self.config.tool_xml_file}"
                    )
                elif abs(tool.diameter - diameter) > 0.1:
                    errors.append(
                        f"Spindle {spindle_id} diameter mismatch: expected {diameter}mm, got {tool.diameter}mm"
                    )
        return errors


def generate_drill_test(config: DrillTestConfig) -> str:
    """
    Convenience function to generate a drill test CIX file.

    Args:
        config: Configuration object with all settings

    Returns:
        Generated CIX content
    """
    generator = CIXGenerator(config)
    return generator.generate_cix()


def generate_all_cix_from_tooling_folder(config: DrillTestConfig, tooling_folder: str = "tooling") -> None:
    """
    Generate CIX files for all XML files in the specified tooling folder.

    Args:
        config: The DrillTestConfig object to use for generation.
        tooling_folder: The folder containing XML files.
    """
    if not os.path.exists(tooling_folder):
        print(f"❌ Tooling folder not found: {tooling_folder}")
        return

    # Find all XML files in the tooling folder
    xml_files = glob.glob(os.path.join(tooling_folder, "*.xml"))

    if not xml_files:
        print(f"❌ No XML files found in tooling folder: {tooling_folder}")
        return

    for xml_file in xml_files:
        print(f"🔄 Processing XML file: {xml_file}")
        config.set_tool_xml_file(xml_file)

        # Create a CIXGenerator instance and generate the CIX file
        generator = CIXGenerator(config)
        try:
            generator.generate_cix()
        except Exception as e:
            print(f"❌ Failed to generate CIX for {xml_file}: {e}")

    print("✅ All CIX files generated.")
