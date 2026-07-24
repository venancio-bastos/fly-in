from render import Renderer


def main() -> None:
    renderer = Renderer()
    running = True

    try:
        while running:
            running = renderer.events_handle()
            renderer.draw_state(None)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        renderer.cleanup()


if __name__ == "__main__":
    main()
