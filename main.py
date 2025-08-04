#!/usr/bin/env python3
"""
Main script for generating drill test CIX files.
"""

from cix_generator import CIXGenerator
from config import DrillTestConfig, create_config_from_example, example_configs


def main():
    """Main function to generate drill test programs."""
    print("🔧 Biesse Rover Drill Test Generator")
    print("=" * 40)

    # Show available example configurations
    print("\nAvailable example configurations:")
    for name, config in example_configs.items():
        print(f"  - {name}: {config['description']}")

    print("\nUsing 'all_available' configuration to test all tools from XML...")

    # Create configuration
    config = create_config_from_example("all_available")

    # Print configuration details
    print(f"\n{config}")

    # Create generator and show tool summary
    generator = CIXGenerator(config)
    generator.print_tool_summary()

    # Generate the CIX file
    try:
        cix_content = generator.generate_cix()
        print(f"\n✅ Successfully generated {config.output_file}")

        # Show some statistics
        lines = cix_content.split("\n")
        drill_macros = [line for line in lines if "BEGIN MACRO" in line]
        print(f"   📊 Generated {len(drill_macros)} drill operations")
        print(f"   📄 Total lines: {len(lines)}")

    except Exception as e:
        print(f"❌ Error generating CIX: {e}")
        return 1

    return 0


def generate_custom_test():
    """Example of generating a custom drill test."""
    print("\n🛠️  Generating custom drill test...")

    # Create custom configuration
    config = DrillTestConfig()
    config.set_start_position(50.0, 100.0)
    config.set_spacing(40.0, 60.0)
    config.set_drill_depth(18.0)
    config.output_file = "custom_drill_test.cix"

    # Use specific tools (diameter -> spindle IDs)
    custom_tools = {
        5.0: [7, 8, 9, 13, 14],  # 5mm drills
        8.0: [10, 12, 15, 17],  # 8mm drills
        12.0: [2],  # 12mm drill
    }
    config.set_custom_tools(custom_tools)

    print(f"Configuration: {config}")

    # Generate
    try:
        generator = CIXGenerator(config)

        # Validate spindles exist in XML
        errors = generator.validate_spindles(custom_tools)
        if errors:
            print("⚠️  Validation warnings:")
            for error in errors:
                print(f"   - {error}")

        generator.generate_cix()
        print(f"✅ Custom test generated: {config.output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run main generator
    result = main()

    # Optionally generate a custom test as well
    print("\n" + "=" * 40)
   # generate_custom_test()

    exit(result)
