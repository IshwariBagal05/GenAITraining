from app.records import load_records, search, count_by, get_by_id


def display_record(r):
    print("\n" + "-" * 50)
    print(f"ID:             {r['id']}")
    print(f"Topic:          {r['topic']}")
    print(f"Insurance type: {r['insurance_type']}")
    print(f"Rule summary:   {r['rule_summary']}")
    print(f"Time limit:     {r['time_limit']}")
    print(f"Who to contact: {r['who_to_contact']}")
    print(f"Source:         {r['source_url']}")


def main():
    records = load_records()
    if not records:
        return

    while True:
        print("\n========== INSURECLEAR ==========")
        print("1. Display all records")
        print("2. Search by keyword")
        print("3. Count by insurance category")
        print("4. Get record by ID")
        print("0. Exit")
        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            for r in records:
                display_record(r)
            input("\nPress Enter to return to the menu...")
        elif choice == "2":
            results = search(records, input("Enter keyword: "))
            if results:
                for r in results:
                    display_record(r)
            else:
                print("No matching records.")
        elif choice == "3":
            print("\nRECORDS PER INSURANCE CATEGORY")
            counts = count_by(records, "insurance_type")
            for category, n in sorted(counts.items()):
                print(f"{category:20} {n}")
            print(f"{'TOTAL':20} {sum(counts.values())}")
            input("\nPress Enter to return to the menu...")
        elif choice == "4":
            try:
                r = get_by_id(records, int(input("Enter ID: ")))
            except ValueError:
                print("Enter a valid number.")
                continue
            display_record(r) if r else print("Not found.")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()