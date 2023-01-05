import aiohttp
import asyncio
import os


API_ENDPOINT = os.getenv(
    'IRG_ENDPOINT')
GENERATED_PDFS_DIR = os.getenv(
    'PDFS_DIR')
print(f'API_ENDPOINT = {API_ENDPOINT}')
print(f'GENERATED_PDFS_DIR  = {GENERATED_PDFS_DIR}')


def getJsonData(language, book):
    jsonData = {
        'assembly_strategy_kind': 'blo',
        'layout_for_print': False,
        'resource_requests': [],
        'generate_pdf': True,
        'generate_epub': False,
        'generate_docx': False
    }

    for resource in language['resources']:
        jsonData['resource_requests'].append({
            'lang_code': language['lang_code'],
            'resource_type': resource,
            'resource_code': book['book_code']
        })

    return jsonData


async def generate(language, book):
    jsonData = getJsonData(language, book)
    timeout = aiohttp.ClientTimeout(total=900)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_ENDPOINT, json=jsonData, timeout=timeout) as response:
                json = await response.json()
                status = response.status

                if (status == 200):
                    return GENERATED_PDFS_DIR + json['finished_document_request_key'] + ".pdf"
                else:
                    print('')
                    print(
                        f'REST error for {language["lang_name"]} {book["book_name"]}')
                    print(status)
                    print(json)
                    print('')
                    return None
    except asyncio.TimeoutError:
        print('')
        print(f'Timeout error for {language["lang_name"]} {book["book_name"]}')
        print('')
        return None
