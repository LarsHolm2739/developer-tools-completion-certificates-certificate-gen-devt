import argparse

from src.certificate_service import BuildEvent, service_from_environment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", required=True)
    args = parser.parse_args()
    event = BuildEvent(
        participant="Ada Lovelace",
        repository="release-tools",
        release_tag="v1.4.0",
        recipient=args.recipient,
    )
    result = service_from_environment().complete_release(event)
    print(f"certificate={result.pdf_reference}")
    print(f"message_id={result.message_id}")


if __name__ == "__main__":
    main()
