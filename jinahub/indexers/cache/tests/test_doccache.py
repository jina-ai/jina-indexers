import os

from jina import Flow, DocumentArray, Document

from .. import DocCache

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_cache_content_hash(tmpdir):
    os.environ['CACHE_FIELDS'] = '[content_hash]'
    os.environ['CACHE_WORKSPACE'] = os.path.join(tmpdir, 'cache')
    docs = [Document(content='a'), Document(content='a')]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs:
        d.update_content_hash()

    docs2 = [Document(content='b'), Document(content='a')]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs2:
        d.update_content_hash()

    with Flow(return_results=True).add(uses=os.path.join(cur_dir, 'cache.yml')) as f:
        response = f.post(
            on='/index',
            inputs=DocumentArray(docs),
        )
        assert len(response[0].docs) == 1
        assert set([d.content for d in response[0].docs]) == {'a'}

        response = f.post(
            on='/index',
            inputs=DocumentArray(docs2),
        )
        assert len(response[0].docs) == 1
        # assert the correct docs have been removed
        assert set([d.content for d in response[0].docs]) == {'b'}


def test_cache_id(tmpdir):
    os.environ['CACHE_FIELDS'] = '[id]'
    os.environ['CACHE_WORKSPACE'] = os.path.join(tmpdir, 'cache')
    docs = [Document(id='a'), Document(id='a')]

    docs2 = [Document(id='b'), Document(id='a')]

    with Flow(return_results=True).add(uses=os.path.join(cur_dir, 'cache.yml')) as f:
        response = f.post(
            on='/index',
            inputs=DocumentArray(docs),
        )
        assert len(response[0].docs) == 1
        # assert the correct docs have been removed
        assert set([d.id for d in response[0].docs]) == {'a'}

        response = f.post(
            on='/index',
            inputs=DocumentArray(docs2),
        )
        assert len(response[0].docs) == 1
        # assert the correct docs have been removed
        assert set([d.id for d in response[0].docs]) == {'b'}


def test_cache_id_content_hash(tmpdir):
    os.environ['CACHE_FIELDS'] = '[id, content]'
    os.environ['CACHE_WORKSPACE'] = os.path.join(tmpdir, 'cache')
    docs = [
        Document(id='a', content='content'),
        Document(id='a', content='content'),
        Document(id='a', content='content'),
    ]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs:
        d.update_content_hash()

    with Flow(return_results=True).add(uses=os.path.join(cur_dir, 'cache.yml')) as f:
        response = f.post(
            on='/index',
            inputs=DocumentArray(docs),
        )
        assert len(response[0].docs) == 1
        # assert the correct docs have been removed
        assert set([d.content for d in response[0].docs]) == {'content'}
        assert set([d.id for d in response[0].docs]) == {'a'}


def test_cache_id_content_hash2(tmpdir):
    os.environ['CACHE_FIELDS'] = '[id, content_hash]'
    os.environ['CACHE_WORKSPACE'] = os.path.join(tmpdir, 'cache')
    docs2 = [
        Document(id='b', content='content'),
        Document(id='a', content='content'),
        Document(id='a', content='content'),
    ]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs2:
        d.update_content_hash()

    with Flow(return_results=True).add(uses=os.path.join(cur_dir, 'cache.yml')) as f:
        response = f.post(
            on='/index',
            inputs=DocumentArray(docs2),
        )
        assert len(response[0].docs) == 2


def test_cache_crud(tmpdir):
    docs = [
        Document(id=1, content='content'),
        Document(id=2, content='content'),
        Document(id=3, content='content'),
        Document(id=4, content='content2'),
    ]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs:
        d.update_content_hash()

    cache = DocCache(
        fields=('content_hash',),
        metas={'workspace': os.path.join(tmpdir, 'cache'), 'name': 'cache'},
        runtime_args={'pea_id': 0},
    )
    cache.index_or_remove_from_request(docs)
    # we cache all the docs by id, we just remove the ones that have already been "hit"
    assert cache.ids_count == 4
    assert cache.hashes_count == 2

    docs = [
        Document(id=1, content='content3'),
        Document(id=2, content='content4'),
        Document(id=3, content='contentX'),
        Document(id=4, content='contentBLA'),
    ]
    # to remove once https://github.com/jina-ai/jina/pull/2673 is merged
    for d in docs:
        d.update_content_hash()

    cache.update(docs)
    assert cache.ids_count == 4
    assert cache.hashes_count == 4

    docs = [
        Document(id=1),
        Document(id=2),
        Document(id=3),
        Document(id=4),
        Document(id=4),
        Document(id=5),
        Document(id=6),
        Document(id=7),
    ]

    cache.delete(docs)
    assert cache.ids_count == 0
    assert cache.hashes_count == 0
