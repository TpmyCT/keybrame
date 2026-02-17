#!/usr/bin/env python3

def print_banner(title, width=60):
    """Imprime un banner formateado"""
    print("=" * width)
    print(f"  {title}")
    print("=" * width)

def print_info(items, width=60):
    """Imprime items de información"""
    for key, value in items.items():
        print(f"{key}: {value}")
    print("=" * width)

def print_startup_message(shutdown_combo):
    """Mensaje de inicio del servidor"""
    print("\n>> Servidor iniciado.")
    print("   - Para detener: Click derecho en icono del system tray -> Detener servidor")
    print(f"   - O presiona {'+'.join(shutdown_combo)}\n")
