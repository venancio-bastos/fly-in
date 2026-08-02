from src.render import Renderer
import sys

def main() -> None:
    renderer = Renderer()
    running = True

    if len(sys.argv) < 2:
        print("ERROR: A level must passed.")
        sys.exit(1)

    file_name = sys.argv[1]
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                drones_parsed = False

                if not line or line.startswith('#'):
                    continue

                if not line.startswith("nb_drones:") and not drones_parsed:
                    print("ERROR: 'nb_drones' missing or its not in first line")
                    sys.exit(1)
                else:
                    number = line.split("nb_drones:")
                    if not number[1].strip().isnumeric():
                        print(f"ERROR: 'nb_drones' amount its invalid -> {number[1]}")
                        sys.exit(1)

    except FileNotFoundError:
        print(f"ERROR: File {file_name} not found.")

    try:
        while running:
            running = renderer.events_handle()
            renderer.draw_state(None)
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        renderer.cleanup()


if __name__ == "__main__":
    main()
