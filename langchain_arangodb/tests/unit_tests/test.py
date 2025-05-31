import os
import ast
from arango import ArangoClient
from arango.database import StandardDatabase
from pathlib import Path
from typing import Union


def get_db_connection() -> StandardDatabase:
    client = ArangoClient()
    db = client.db('_system', username='root', password='openSesame')
    return db


def create_collections(db: StandardDatabase):
    collections = [
        ('directory', False),
        ('nodes', False),
        ('edges', True)
    ]
    for name, is_edge in collections:
        if not db.has_collection(name):
            db.create_collection(name, edge=is_edge)
            print(f"Created collection: {name}")
        else:
            print(f"Collection already exists: {name}")


def sanitize_key(path: str) -> str:
    return path.replace(os.sep, '_').replace('.', '_')


def parse_python_file(file_path: str, parent_file_key: str, db: StandardDatabase):
    nodes_col = db.collection('nodes')
    edges_col = db.collection('edges')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            class_key = f"{parent_file_key}_{node.name}"
            class_doc = {
                '_key': class_key,
                'type': 'class',
                'name': node.name,
                'defined_in': parent_file_key,
                'lineno': node.lineno
            }
            try:
                nodes_col.insert(class_doc, overwrite=True)
                edges_col.insert({
                    '_from': f'nodes/{parent_file_key}',
                    '_to': f'nodes/{class_key}',
                    'type': 'defines',
                    'perspective': 'class-structure'
                })
                print(f"Inserted class: {node.name} in {file_path}")
            except Exception as e:
                print(f"Failed to insert class {node.name}: {e}")
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef):
            func_key = f"{parent_file_key}_{node.name}"
            func_doc = {
                '_key': func_key,
                'type': 'function',
                'name': node.name,
                'defined_in': parent_file_key,
                'lineno': node.lineno
            }
            try:
                nodes_col.insert(func_doc, overwrite=True)
                edges_col.insert({
                    '_from': f'nodes/{parent_file_key}',
                    '_to': f'nodes/{func_key}',
                    'type': 'defines',
                    'perspective': 'function-structure'
                })
                print(f"Inserted function: {node.name} in {file_path}")
            except Exception as e:
                print(f"Failed to insert function {node.name}: {e}")

    visitor = Visitor()
    visitor.visit(tree)


def insert_directory_and_file_documents(db: StandardDatabase, base_dir: str):
    directory_col = db.collection('directory')
    nodes_col = db.collection('nodes')
    edges_col = db.collection('edges')

    for root, dirs, files in os.walk(base_dir):
        rel_root = os.path.relpath(root, base_dir)
        dir_key = sanitize_key(rel_root) if rel_root != '.' else sanitize_key(Path(base_dir).name)

        dir_doc = {
            '_key': dir_key,
            'type': 'directory',
            'path': os.path.abspath(root)
        }
        try:
            directory_col.insert(dir_doc, overwrite=True)
            print(f"Inserted directory: {dir_doc['path']}")
        except Exception as e:
            print(f"Failed to insert directory {dir_doc['path']}: {e}")

        parent_dir = os.path.dirname(rel_root)
        if parent_dir and parent_dir != '.':
            parent_key = sanitize_key(parent_dir)
            try:
                edges_col.insert({
                    '_from': f'directory/{parent_key}',
                    '_to': f'directory/{dir_key}',
                    'type': 'contains',
                    'perspective': 'file-structure'
                })
            except Exception as e:
                print(f"Failed to insert edge for directory {dir_key}: {e}")

        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_key = sanitize_key(os.path.relpath(file_path, base_dir))
            file_doc = {
                '_key': file_key,
                'type': 'file',
                'name': file_name,
                'path': os.path.abspath(file_path)
            }
            try:
                nodes_col.insert(file_doc, overwrite=True)
                print(f"Inserted file: {file_doc['path']}")
                edges_col.insert({
                    '_from': f'directory/{dir_key}',
                    '_to': f'nodes/{file_key}',
                    'type': 'contains',
                    'perspective': 'file-structure'
                })
                if file_name.endswith('.py'):
                    parse_python_file(file_path, file_key, db)
            except Exception as e:
                print(f"Failed to insert file {file_path}: {e}")


def main():
    base_dir = "C:\workspace\langchain-neo4j"  # TODO: replace with your actual project directory
    db = get_db_connection()
    create_collections(db)
    insert_directory_and_file_documents(db, base_dir)


if __name__ == "__main__":
    main()