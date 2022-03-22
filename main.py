from Scheduler import Scheduler

if __name__ == "__main__":
    sheet_name = input('Podaj nazwe arkusza: \n')
    person_name = input('Podaj imię i nazwisko: \n')
    scheduler = Scheduler(sheet_name, person_name)
    scheduler.execute()
