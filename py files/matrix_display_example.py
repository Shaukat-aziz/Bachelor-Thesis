#!~/mamabaforge/envs/pymeep_env/bin/python
"""
Example of the new matrix display format for atom positions.
This demonstrates how atoms will be displayed in the GUI.
"""

# Example atom positions (list of [x, y] pairs)
atoms = [
    [-0.123456, -0.654321],
    [0.234567, 0.876543],
    [-0.345678, 0.456789],
    [0.567890, -0.098765],
    [0.789012, 0.321098],
]

def format_atom_matrix(atoms_list):
    """Format atom positions as NumPy-style matrix."""
    matrix_str = "[\n"
    for i, (x_val, y_val) in enumerate(atoms_list):
        matrix_str += f"  [{x_val:>10.6f}  {y_val:>10.6f}]"
        if i < len(atoms_list) - 1:
            matrix_str += "\n"
    matrix_str += "\n]"
    return matrix_str

# Generate and display the matrix
print("Example Atom Matrix Display:")
print("=" * 50)
print(format_atom_matrix(atoms))
print("=" * 50)

print("\n\nEditable Example (user can modify x, y values):")
print("User can edit coordinates directly in this format")
print("and click 'Apply Manual Edits' to regenerate pentagon structure")
