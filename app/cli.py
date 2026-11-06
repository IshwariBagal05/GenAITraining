
from app.records import (
    load_records,
    search,
    count_by,
    get_by_id
)


def display_record(record):

    print("\n" + "=" * 50)
    print(f"ID            : {record['id']}")
    print(f"Topic         : {record['topic']}")
    print(f"Insurance Type: {record['insurance_type']}")
    print(f"Rule Summary  : {record['rule_summary']}")
    print(f"Time Limit    : {record['time_limit']}")
    print(f"Contact       : {record['who_to_contact']}")
    print(f"Source URL    : {record['source_url']}")
    print("=" * 50)


def main():

    records = load_records()

    print("\nWelcome to InsureClear!")
    print(f"Total records loaded: {len(records)}")

    while True:

        print("\n========== INSURECLEAR ==========")
        print("1. Display All Records")
        print("2. Search by Keyword")
        print("3. Count by Insurance Category")
        print("4. Get Record by ID")
        print("0. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            print("\nALL INSURANCE RECORDS")
            for record in records:
                display_record(record)
                input("\nPress Enter to return to the menu...")

        elif choice == "2":

            keyword = input("Enter keyword: ")

            results = search(records, keyword)

            if results:
                print(f"\nFound {len(results)} records.")

                for record in results:
                    display_record(record)
            else:
                print("No matching records found.")

        elif choice == "3":

            counts = count_by(records, "insurance_type")

            print("\nINSURANCE CATEGORY COUNTS")

            for category, total in sorted(counts.items()):
                print(f"{category}: {total}")

        elif choice == "4":

            record_id = input("Enter record ID: ")

            record = get_by_id(records, record_id)

            if record:
                display_record(record)
            else:
                print("Record not found.")

        elif choice == "0":

            print("Thank you for using InsureClear!")
            break

        else:

            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
