from typing import List

class MockFileMetadata:
    def __init__(self, name: str, path_lower: str):
        self.name = name
        self.path_lower = path_lower

class MockListFolderResult:
    def __init__(self, entries: str, has_more: str):
        self.entries = entries
        self.has_more = has_more

class MockSearchMatch:
    def __init__(self, metadata: List[MockFileMetadata]):
        self.metadata = metadata

class MockSearchResult:
    def __init__(self, matches: List[MockSearchMatch]):
        self.matches = matches

class MockPathLinkMetadata:
    def __init__(self, url: str):
        self.url = url

class MockHttpResponse:
    def __init__(self, text: str):
        self.text = text
