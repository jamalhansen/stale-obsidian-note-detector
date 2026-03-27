from stale_obsidian_note_detector.logic import count_links

def test_count_links():
    content = "This is a [[Link 1]] and another [[Link 2]]."
    assert count_links(content) == 2
    
    assert count_links("No links here.") == 0
    assert count_links("[[One link]]") == 1
