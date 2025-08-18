#!/usr/bin/env python3
"""
Main script for generating drill test CIX files.
"""

from cix_generator import CIXGenerator, generate_all_cix_from_tooling_folder
from config import DrillTestConfig, create_config_from_example, example_configs


def main():
    """Main function to generate drill test programs for all XML files in tooling."""
    print("🔧 Biesse Rover Drill Test Generator")
    print("=" * 40)

    # Create configuration
    config = DrillTestConfig()

    # Generate CIX files for all XML files in the tooling folder
    tooling_folder = "tooling"
    generate_all_cix_from_tooling_folder(config, tooling_folder)


if __name__ == "__main__":
    # Run main generator
    main()
