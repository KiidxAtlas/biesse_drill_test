# Biesse Rover Drill Test Generator

A Python-based CIX file generator for creating automated drill test programs for Biesse Rover CNC machines. This tool reads XML tool configuration files and generates comprehensive drill test programs with engraving labels showing diameter and tool count information.

## Features

- 🔧 **XML Tool Parsing**: Reads Biesse tool XML files to extract spindle and diameter information
- 📝 **CID3 Format Output**: Generates properly formatted CIX files compatible with Biesse Rover machines
- 🏷️ **Automatic Engraving**: Creates text labels showing diameter and tool count (e.g., "5.0mm - 10")
- 🎯 **Flexible Configuration**: Support for custom tool selections, spacing, positioning, and depths
- 🔄 **Spindle Cycling**: Cycles through all specified spindles, using different spindles for each hole
- ✅ **Validation**: Validates tool configurations against available XML data
- 📊 **Multiple Modes**: Test all tools, specific diameters, or custom spindle selections

## Quick Start

### Basic Usage

```python
from config import DrillTestConfig
from cix_generator import CIXGenerator

# Create configuration
config = DrillTestConfig()
config.enable_all_tools_test()  # Test all tools from XML

# Generate CIX file
generator = CIXGenerator(config)
generator.generate_cix()
```

### Run the Generator

```bash
python main.py              # Generate test with all available tools
```

## Configuration Options

### Basic Settings

```python
config = DrillTestConfig()

# Positioning and spacing
config.set_start_position(50.0, 100.0)    # Starting X, Y coordinates
config.set_spacing(40.0, 60.0)            # X spacing, Y spacing between holes
config.set_drill_depth(15.0)              # Drill depth in mm

# Output file
config.output_file = "my_drill_test.cix"

# Tool XML source
config.set_tool_xml_file("R3_tools.xml")
```

### Tool Selection Modes

#### 1. Test All Available Tools
```python
config.enable_all_tools_test()
```

#### 2. Test Specific Diameters and Spindles
```python
custom_tools = {
    5.0: [7, 8, 9, 13, 14],     # 5mm drills using spindles 7-14
    8.0: [10, 12, 15, 17],      # 8mm drills using spindles 10,12,15,17
    12.0: [2]                   # 12mm drill using spindle 2
}
config.set_custom_tools(custom_tools)
```

#### 3. Use Predefined Examples
```python
from config import create_config_from_example

config = create_config_from_example('small_holes')    # 3-6mm holes
config = create_config_from_example('medium_holes')   # 8-12mm holes
config = create_config_from_example('large_holes')    # 15-35mm holes
```

## Generated Output

The generator creates CIX files with:

### 1. CID3 Header Structure
```
BEGIN ID CID3
    REL=5.0
END ID

BEGIN MAINDATA
    LPX=438.0
    LPY=640.0
    ...
END MAINDATA
```

### 2. Engraving Labels (GEOTEXT + ROUTG)
For each diameter group, creates engraved text showing:
- Diameter in mm
- Number of available tools
- Example: "5.0mm - 10" means 5.0mm diameter with 10 tools

### 3. Drill Operations (BG Macros)
For each spindle, creates a drill operation with:
- Specific spindle assignment (SPI parameter)
- Diameter matching the tool
- Configured depth and position
- Proper CIX formatting

## File Structure

```
drill_cix_generator/
├── config.py              # Configuration classes and examples
├── cix_generator.py        # Core CIX generation logic
├── main.py                # Main execution script
├── examples_new.py        # Example usage scenarios
├── R3_tools.xml           # Tool configuration (R3 setup)
├── toolsR1.xml           # Tool configuration (R1 setup)
├── toolsR2.xml           # Tool configuration (R2 setup)
└── *.cix                 # Generated output files
```

## XML Tool File Format

The generator supports XML files with this structure:

```xml
<Tooling>
    <Spindle Name="1" Child="D10" />
    <Spindle Name="2" Child="D12" />
    <Spindle Name="3" Child="D10" />
    ...
</Tooling>
```

Where:
- `Name` = Spindle ID number
- `Child` = Tool diameter (format: "D{diameter}")

## Example Configurations

### Small Holes Test (3-6mm)
```python
config = create_config_from_example('small_holes')
# Tests: 3.0mm(1), 4.0mm(3), 5.0mm(10), 6.0mm(1) tools
# Spacing: 25mm x 40mm
# Depth: 12mm
```

### Custom Large Tools Test
```python
config = DrillTestConfig()
config.set_start_position(100.0, 150.0)
config.set_spacing(50.0, 80.0)
config.set_drill_depth(20.0)

large_tools = {
    12.0: [2],      # 12mm
    15.0: [5],      # 15mm
    20.0: [26],     # 20mm
    35.0: [11]      # 35mm
}
config.set_custom_tools(large_tools)
```

## Validation and Error Checking

The system validates:
- ✅ XML file existence and format
- ✅ Spindle IDs exist in XML
- ✅ Diameter matching between config and XML
- ✅ Spacing and depth within safety limits
- ✅ Tool count limits per row

```python
generator = CIXGenerator(config)
errors = generator.validate_spindles(custom_tools)
if errors:
    for error in errors:
        print(f"⚠️ {error}")
```

## Output Statistics

Each generation provides:
- 📊 Number of drill operations created
- 📄 Total CIX file lines
- 🔧 Tool summary by diameter
- ✅ Success/error status

## Production Usage

### Standard Workflow
1. Configure your drill test parameters in `config.py` or create a custom configuration
2. Run `python main.py` to generate the CIX file
3. Transfer the generated `.cix` file to your Biesse Rover machine
4. Load and run the program to verify tool performance

### File Structure
```
drill_cix_generator/
├── main.py              # Main execution script
├── config.py            # Configuration management
├── cix_generator.py     # Core CIX generation logic
├── R3_tools.xml         # Primary tool configuration
├── toolsR1.xml          # Alternative tool set 1
├── toolsR2.xml          # Alternative tool set 2
└── README.md            # This documentation
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)
- Biesse tool XML files
- Basic understanding of CIX format

## Usage Tips

1. **Start with defaults**: Run `python main.py` for a comprehensive test using all available tools
2. **Validate first**: Always check validation errors before running on machine
3. **Test incrementally**: Start with small tool sets before running comprehensive tests
4. **Check spacing**: Ensure adequate spacing for your workpiece size
5. **Verify depths**: Match drill depths to your material thickness and requirements

## Troubleshooting

### Common Issues

**"Tool XML file not found"**
- Ensure XML file exists in the project directory
- Check file path in config.tool_xml_file

**"Spindle X not found in XML"**
- Verify spindle ID exists in your XML file
- Check spelling of XML file format

**"Spacing too small"**
- Increase X/Y spacing values
- Check min_spacing configuration (default: 20mm)

**"No tools configured"**
- Ensure either test_all_tools=True OR custom_tool_config is set
- Verify XML file contains valid tool data

## License

This project is for internal use with Biesse Rover CNC machines.
