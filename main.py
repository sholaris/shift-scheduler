from Scheduler import Scheduler

if __name__ == "__main__":
    sheet_name = input('Enter spreadsheet name: \n')
    worker = input('Enter your full name: \n')
    scheduler = Scheduler(sheet_name, worker)
    scheduler.execute()

