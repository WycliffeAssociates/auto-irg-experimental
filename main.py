import time
import asyncio
import Resources
import PDF
import json
import os
import schedule
import logging
import datetime


async def launchThread(task, final_list, completed, running):
    language = task['language']
    book = task['book']
    subcontents_array = task['subcontents_array']

    print(
        f'Starting thread for {language["lang_name"]} {book["book_code"]} at {time.asctime()}')

    url = await PDF.generate(language, book)

    if (url != None):
        subcontents_array.append({
            'sort': book['sort_order'],
            'category': book['book_category'],
            'code':  book['book_code'],
            'name': book['book_name'],
            'links': [
                {
                    'url': url,
                    'zipContent': '',
                    'quality': '',
                    'format': 'pdf'
                }
            ]
        })

        # Writing to json output
        json_object = json.dumps(final_list, indent=2)
        with open('/app/output/pdfs.json', 'w') as outfile:
            outfile.write(json_object)

    print(
        f'Finished thread for {language["lang_name"]} {book["book_code"]} at {time.asctime()} --- {url}')
    # Make Atomic
    completed += 1
    running -= 1


def stub_base_json(lang, final_list):
    subcontents_array = []
    lang_stub = {
        'code': lang.get('lang_code'),
        'contents': [
            {
                'subject': 'Interleaved Resources Documents',
                'checkingLevel': '3',
                'subcontents': subcontents_array,
                'code': 'irg',
                'name': 'Interleaved Resources Documents',
                'subject': 'translation notes',
                'links': [
                ]
            }
        ]
    }
    final_list.append(lang_stub)
    return subcontents_array


async def main(threads, runTime):
    print(f'Running {threads} threads for {runTime} minutes.')

    # Variables to reinit at start each time this scheduled process runs main;
    tasks = []
    completed = 0
    running = 0
    final_list = []
    isRunning = True
    # Return the time in seconds since the epoch as a floating point number.
    startTime = time.time()
    endTime = startTime + (runTime * 60)  # i.e. start plus runTime in secs
    runningTasks = set()
    languages = Resources.getLanguages()
    books = Resources.getBooks()

    # Nested Loop will generate a request for Each book in each langauage.
    # Stub base json will return a reference to the array that populates the books for the job that consumes this json to populate biel
    for language in languages:
        subcontents_array = stub_base_json(language, final_list)
        for book in books:
            tasks.append({
                'language': language,
                'book': book,
                'subcontents_array': subcontents_array
            })

    while isRunning:
        if (completed == len(tasks)):
            break
        elif (runTime != -1) and (time.time() > endTime):
            # finish this task; Scheduler should resume next iteration
            break
        elif (running != threads) and (completed + running < len(tasks)):
            nextTask = tasks[completed + running]
            running += 1

            task = asyncio.create_task(launchThread(
                nextTask, final_list, completed, running))
            task.add_done_callback(runningTasks.discard)
            runningTasks.add(task)
        else:
            if (len(runningTasks) != 0):
                await asyncio.wait(runningTasks, return_when=asyncio.FIRST_COMPLETED)

    if (len(runningTasks) != 0):
        print('Shutting down. Finishing current tasks')
        await asyncio.wait(runningTasks)
    print('All tasks done')
    return  # All done with this iteration once the running tasks finish


# Schedule and kickoff the process
threads = int(os.getenv(
    'THREAD_COUNT', 1))
runTime = int(os.getenv(
    'MAX_RUN_TIME_IN_MINS', -1))
runEvery = int(os.getenv(
    'RUN_EVERY_NUM_DAYS', 1))
startTime = os.getenv(
    'RUN_AT_TIME', '00:00:01')


def scheduled_irg_job():
    logging.warning(datetime.datetime.now())
    logging.warning(f'Running {threads} threads for {runTime} minutes.')
    return asyncio.run(main(threads, runTime))


schedule.every(runEvery).days.at(startTime).do(scheduled_irg_job)


while True:
    n = schedule.idle_seconds()
    if n is None:  # 0
        logging.warning(f'No jobs. Exiting...')
        # no more jobs
        break
    elif n > 0:
        # sleep exactly the right amount of time
        logging.warning(datetime.datetime.now())
        logging.warning(f'sleeping for {n} seconds')
        time.sleep(n)
    schedule.run_pending()
