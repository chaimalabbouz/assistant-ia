from pathlib import Path
import fitz


PDF_PATH = Path("data/raw/clark_county_hr_manual.pdf")


def main():
    doc = fitz.open(PDF_PATH)

    # On cherche la page contenant la vraie Policy No. 3.0
    for page_num, page in enumerate(doc):
        text = page.get_text("text")

        if "Policy No. 3.0" in text:
            print("=" * 100)
            print(f"PAGE TROUVÉE : {page_num + 1}")
            print("=" * 100)
            print(repr(text))

            # afficher également les 2 pages suivantes
            for next_page in range(page_num + 1, min(page_num + 3, len(doc))):
                print("\n" + "=" * 100)
                print(f"PAGE {next_page + 1}")
                print("=" * 100)
                print(repr(doc[next_page].get_text("text")))

            break


if __name__ == "__main__":
    main()