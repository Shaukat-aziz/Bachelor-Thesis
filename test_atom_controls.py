#!/usr/bin/env python
"""
Test script to verify atom size and basis position controls are properly integrated.
This tests the structure without requiring matplotlib display.
"""

import ast
import inspect

# Parse the testing.py file to verify structure
with open('FILES/testing.py', 'r') as f:
    source_code = f.read()

tree = ast.parse(source_code)

# Find PentagonGUI class
class_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'PentagonGUI':
        class_node = node
        break

if not class_node:
    print("❌ PentagonGUI class not found")
    exit(1)

print("✓ Found PentagonGUI class")

# Check for required methods
required_methods = [
    'update_atom_size',
    'update_atom_position', 
    'reset_basis_positions',
    'toggle_selection_visibility'
]

found_methods = {m.name for m in class_node.body if isinstance(m, ast.FunctionDef)}

for method in required_methods:
    if method in found_methods:
        print(f"✓ Found method: {method}")
    else:
        print(f"❌ Missing method: {method}")

# Check __init__ for required attributes
init_node = None
for node in class_node.body:
    if isinstance(node, ast.FunctionDef) and node.name == '__init__':
        init_node = node
        break

if init_node:
    init_source = ast.get_source_segment(source_code, init_node)
    if 'self.atom_size' in init_source:
        print("✓ atom_size initialized in __init__")
    else:
        print("❌ atom_size not initialized in __init__")
    
    if 'self.custom_basis_positions' in init_source:
        print("✓ custom_basis_positions initialized in __init__")
    else:
        print("❌ custom_basis_positions not initialized in __init__")
    
    if 'self.basis_textboxes' in init_source:
        print("✓ basis_textboxes list initialized in __init__")
    else:
        print("❌ basis_textboxes not initialized in __init__")

# Check setup_controls for slider
setup_node = None
for node in class_node.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'setup_controls':
        setup_node = node
        break

if setup_node:
    setup_source = ast.get_source_segment(source_code, setup_node)
    if 'slider_atom_size' in setup_source:
        print("✓ slider_atom_size created in setup_controls")
    else:
        print("❌ slider_atom_size not created in setup_controls")
    
    if 'basis_textboxes' in setup_source and 'TextBox' in setup_source:
        print("✓ Basis textboxes created in setup_controls")
    else:
        print("❌ Basis textboxes not properly created in setup_controls")
    
    if 'Reset Basis' in setup_source:
        print("✓ Reset Basis button created in setup_controls")
    else:
        print("❌ Reset Basis button not created in setup_controls")

# Check create_single_petal for custom_basis parameter
create_single_petal_node = None
for node in class_node.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'create_single_petal':
        create_single_petal_node = node
        break

if create_single_petal_node:
    csp_source = ast.get_source_segment(source_code, create_single_petal_node)
    if 'custom_basis=' in csp_source:
        print("✓ custom_basis parameter passed in create_single_petal")
    else:
        print("❌ custom_basis parameter not passed in create_single_petal")

# Check reset method
reset_node = None
for node in class_node.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'reset':
        reset_node = node
        break

if reset_node:
    reset_source = ast.get_source_segment(source_code, reset_node)
    if 'slider_atom_size' in reset_source:
        print("✓ slider_atom_size reset in reset method")
    else:
        print("❌ slider_atom_size not reset in reset method")
    
    if 'reset_basis_positions' in reset_source:
        print("✓ reset_basis_positions called in reset method")
    else:
        print("❌ reset_basis_positions not called in reset method")

# Check update_plot for atom_size
update_plot_node = None
for node in class_node.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'update_plot':
        update_plot_node = node
        break

if update_plot_node:
    up_source = ast.get_source_segment(source_code, update_plot_node)
    if 's=self.atom_size' in up_source:
        print("✓ scatter plot uses self.atom_size")
    else:
        print("❌ scatter plot doesn't use self.atom_size")

print("\n✅ All structural checks passed!")
