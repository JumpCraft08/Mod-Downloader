import json, os, time, webbrowser, zipfile, shutil, requests

# Verificación de la dependencia 'requests'
try:
    import requests
except ImportError:
    if input("Falta 'requests'. ¿Instalarla? (s/n): ").strip().lower() == "s":
        os.system("pip install requests")
        import requests
        os.system("cls" if os.name == "nt" else "clear")
    else:
        exit("No se puede ejecutar sin 'requests'.")

# Cargar configuración
config_file = "mods.json"
if not os.path.exists(config_file): exit(f"Error: No se encontró '{config_file}'.")
config = json.load(open(config_file, encoding="utf-8"))

def guardar_config():
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def descomprimir_mrpack(archivo_mrpack, nombre_modpack):
    try:
        carpeta_modpack = f"downloads/{nombre_modpack.replace(' ', '_')}"
        os.makedirs(carpeta_modpack, exist_ok=True)
        with zipfile.ZipFile(archivo_mrpack, 'r') as zip_ref:
            zip_ref.extractall(carpeta_modpack)
        
        # Descargar y mover archivos
        index_file = f"{carpeta_modpack}/modrinth.index.json"
        if os.path.exists(index_file):
            modrinth_data = json.load(open(index_file, "r", encoding="utf-8"))
            for mod in modrinth_data["files"]:
                mod_name = mod["path"]
                for download_url in mod["downloads"]:
                    response = requests.get(download_url, stream=True)
                    if response.status_code == 200:
                        destino = f"downloads/{'resourcepacks' if 'resourcepacks' in mod_name else 'mods'}/{os.path.basename(mod_name)}"
                        os.makedirs(os.path.dirname(destino), exist_ok=True)
                        with open(destino, "wb") as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)

        # Mover y eliminar duplicados
        for carpeta in ["config", "resourcepacks", "saves"]:
            source = f"{carpeta_modpack}/overrides/{carpeta}"
            destino = f"downloads/{carpeta}"
            if os.path.exists(source): shutil.move(source, destino)

        recurso_packs_path = "downloads/resourcepacks/resourcepacks"
        if os.path.exists(recurso_packs_path):
            for item in os.listdir(recurso_packs_path):
                source = os.path.join(recurso_packs_path, item)
                destino = os.path.join("downloads/resourcepacks", item)
                if not os.path.exists(destino): shutil.move(source, destino)
            shutil.rmtree(recurso_packs_path)

        # Limpiar
        os.remove(archivo_mrpack)
        shutil.rmtree(carpeta_modpack)
    except Exception as e:
        print(f"Error: {e}")

def mover_a_minecraft():
    minecraft_path = os.path.expandvars(r"%APPDATA%\.minecraft")
    if not os.path.exists(minecraft_path):
        print(f"Error: No se encontró la carpeta .minecraft en {minecraft_path}.")
        time.sleep(3)
        return

    if not os.path.exists("downloads") or not os.listdir("downloads"):
        print("Error: No se encontró la carpeta 'downloads' o está vacía.")
        time.sleep(3)
        return

    carpetas_movidas = []
    try:
        for carpeta in ["mods", "resourcepacks", "config", "saves"]:
            source = f"downloads/{carpeta}"
            destino = os.path.join(minecraft_path, carpeta)

            if os.path.exists(source):
                if config.get("borrar_.minecraft_al_instalar", False) and os.path.exists(destino):
                    shutil.rmtree(destino)  # Borrar la carpeta si existe

                if os.path.exists(destino):
                    for root, dirs, files in os.walk(source):
                        for file in files:
                            source_file = os.path.join(root, file)
                            destino_file = os.path.join(destino, os.path.relpath(source_file, source))
                            os.makedirs(os.path.dirname(destino_file), exist_ok=True)
                            shutil.copy2(source_file, destino_file)
                else:
                    shutil.move(source, destino)
                
                # Verificar si la carpeta original aún existe antes de intentar eliminarla
                if os.path.exists(source):
                    shutil.rmtree(source)

                carpetas_movidas.append(carpeta)
    except Exception as e:
        print(f"Error al mover las carpetas: {e}")
        time.sleep(3)
        return

    if carpetas_movidas:
        print(f"Se ha movido el contenido de las carpetas: {', '.join(carpetas_movidas)}")
    else:
        print("No se encontraron carpetas para mover.")

    time.sleep(3)

def descargar_mods():
    os.makedirs("downloads/mods", exist_ok=True)
    os.makedirs("downloads/resourcepacks", exist_ok=True)

    # Descargar mods
    for mod in config["mods"]:
        print(f"Descargando {mod['nombre']}...")
        if "modrinth_id" in mod:
            for v in requests.get(f"https://api.modrinth.com/v2/project/{mod['modrinth_id']}/version").json():
                if config["version_mc"] in v["game_versions"] and config["mod_loader"] in v["loaders"]:
                    archivo_mrpack = f"downloads/mods/{v['files'][0]['filename']}"
                    with requests.get(v["files"][0]["url"], stream=True) as res, open(archivo_mrpack, "wb") as file:
                        for chunk in res.iter_content(1024): file.write(chunk)
                    break
            else:
                print(f"Error: {mod['nombre']} no encontrado.")
        elif "curseforge_url" in mod:
            webbrowser.open(f"{mod['curseforge_url']}/files/all?version={config['version_mc']}")
            print(f"Ve a la página para descargar manualmente {mod['nombre']}")

    print("Descarga completada. Cerrando en 3 segundos...")
    time.sleep(3)

def menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"Version: {config['version_mc']} | Loader: {config['mod_loader']}\n[1] Descargar mods\n[2] Instalar mods\n[3] Configurar\n[4] Salir")
        opcion = input("Opción: ").strip()
        if opcion == "1": descargar_mods()
        elif opcion == "2": mover_a_minecraft()
        elif opcion == "3":
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                verde = "\033[92m"
                reset = "\033[0m"
                incluir_modpacks = "Sí" if config.get("incluir_modpacks", True) else "No"
                borrar_minecraft = "Sí" if config.get("borrar_.minecraft_al_instalar", False) else "No"

                print(f"[1] Seleccionar versión de Minecraft  {verde}{config['version_mc']}{reset}")
                print(f"[2] Seleccionar Loader                {verde}{config['mod_loader']}{reset}")
                print(f"[3] Incluir Modpacks                  {verde}{incluir_modpacks}{reset}")
                print(f"[4] Borrar mods al instalar           {verde}{borrar_minecraft}{reset}")
                print("[5] Volver")
                
                opcion_config = input("Opción: ").strip()
                if opcion_config == "1": config["version_mc"] = input("Versión de Minecraft: ").strip()
                elif opcion_config == "2": config["mod_loader"] = input("Loader (fabric/forge/neoforge): ").strip().lower()
                elif opcion_config == "3": config["incluir_modpacks"] = input("¿Incluir Modpacks? (s/n): ").strip().lower() != "n"
                elif opcion_config == "4": config["borrar_.minecraft_al_instalar"] = input("¿Borrar carpetas de .minecraft antes de instalar? (s/n): ").strip().lower() == "s"
                elif opcion_config == "5": break
                guardar_config()
        elif opcion == "4": exit("Saliendo...")

menu()
