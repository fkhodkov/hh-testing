import requests
from requests.utils import urlparse
import re

api_root = 'https://api.hh.ru/vacancies'
tests = []


def get_response(query):
    response = requests.get(api_root, query)
    res = response.json()
    res.update({'original_url': response.url})
    return res


def get_vacancy(vacancy_id):
    return requests.get(f'{api_root}/{vacancy_id}').text


def is_query_modified(response):
    def params(url):
        return dict(q.split('=') for q in urlparse(url).query.split('&'))
    url_params = params(response['original_url'])
    alt_params = params(response['alternate_url'])
    return url_params['text'] != alt_params['text']


def is_actually_contains_query(response, query):
    vacancies = (get_vacancy(item['id']).lower() for item in response['items'])
    words = re.sub('[!"]', '', query['text'].lower())
    return all(words in v for v in vacancies)


def test(description):
    def inner(fn):
        def _f():
            print('[' + fn.__name__ + ']:', description,
                  '[Passed]' if fn() else '[FAILED]')
        tests.append(_f)
        return fn
    return inner


@test('Простой запрос: должны получить совпадения')
def test_good_query():
    query = {'text': 'Java'}
    res = get_response(query)
    return res['items']


@test('Неверный запрос: не должны получить совпадения')
def test_bad_query():
    query = {'text': 'Javapioakieoau'}
    res = get_response(query)
    return not res['items']


@test('Запрос в несколько слов: получить какие-то совпадения')
def test_multiple_words():
    query = {'text': 'Java проспект'}
    res = get_response(query)
    return res['items']


@test('Вакансии, которые поиск по точному совпадению, \
должны реально содержать искомое слово')
def test_exact_word():
    query = {'text': '!хедхантер'}
    res = get_response(query)
    return is_actually_contains_query(res, query)


@test('Поиск по точному хорошему словосочетанию должен что-то вернуть')
def test_exact_phrase():
    query = {'text': '!"Программист Python"'}
    res = get_response(query)
    return res['items'] and not is_query_modified(res)


@test('Поиск по точному плохому словосочетанию может что-то вернуть, \
только если запрос модифицирован сервером')
def test_wrong_exact_phrase():
    query = {'text': '"Java проспект"'}
    response = get_response(query)
    return not response['items'] or is_query_modified(response)


@test('Поиск по части слова: должны получить совпадения')
def test_good_wildcard():
    query = {'text': 'Java*'}
    res = get_response(query)
    return res['items']


@test('Неверный поиск по части слова: не должны получить совпадения')
def test_bad_wildcard():
    query = {'text': 'Jtpglm*'}
    res = get_response(query)
    return not res['items']


@test('Поиск с OR: должны получить совпадения')
def test_good_or():
    query = {'text': 'Java OR Python'}
    res = get_response(query)
    return res['items']


@test('Неверный поиск с OR: не должны получить совпадения')
def test_bad_or():
    query = {'text': 'Jtvgln OR Plmfgtn'}
    res = get_response(query)
    return not res['items']


@test('Поиск с AND: должны получить совпадения')
def test_good_and():
    query = {'text': 'Java AND Python'}
    res = get_response(query)
    return res['items']


@test('Неверный поиск с AND: не должны получить совпадения')
def test_bad_and():
    query = {'text': 'Jtvgln AND Plmfgtn'}
    res = get_response(query)
    return not res['items']


@test('Поиск с NOT: должны получить совпадения')
def test_good_not():
    query = {'text': 'Java NOT PHP'}
    res = get_response(query)
    return res['items']


@test('Неверный поиск с NOT: не должны получить совпадения')
def test_bad_not():
    query = {'text': 'Jtvgln NOT Plmfgtn'}
    res = get_response(query)
    return not res['items']


@test('Сложный запрос: должны получить совпадения')
def test_good_complex():
    query = {'text': '(Java AND Python) NOT (PHP OR 1С)'}
    res = get_response(query)
    return res['items']


@test('Неверный сложный запрос: не должны получить совпадения')
def test_bad_complex():
    query = {'text': '(Jtvgln AND Plmfgtn) NOT (PHP OR 1С)'}
    res = get_response(query)
    return not res['items']


@test('Поиск по полям: должны получить совпадения')
def test_good_fields():
    query = {'text': '(Java OR Python) AND COMPANY_NAME:HeadHunter'}
    res = get_response(query)
    return res['items']


@test('Неверный поиск по полям: не должны получить совпадения')
def test_bad_fields():
    query = {'text': 'HeadHunter AND COMPANY_NAME:(Java OR Python)'}
    res = get_response(query)
    return not res['items']


for test in tests:
    test()
