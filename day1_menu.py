while True:
    print("======= Insurance Clear ===========")
    print("1. About Insurance Clear")
    print("2. Sample Questions")
    print("3. Insurance rule Book ")
    print("0. Exit")
    print("===================================")

    choice=int(input("Enter your choice "))

    if choice==1:
        print("InsuranceClear help user to understand insurance information")

    elif choice==2:
        print("======== Sample Insurance Questions =========")
        print("1. What is health Insurance ")
        print("2. What is the premium?")
        print("3. What is an insurance Claim?")

    elif choice==3:
        age=int(input("Enter your age "))
        if age<18:
            print("You are not eligible")
        else:
            print("you are eligible")
            
    elif choice==0:
        print("Thank you for using InsuranceClear")
        break
    else:
        print("Invalid choice ")