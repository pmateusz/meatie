import pytest
from meatie.internal.template import PathTemplate


def test_basic_parameter_substitution():
    template = PathTemplate.from_string("/{endpoint}")
    assert template.format(endpoint="users") == "/users"
    assert template.parameters == ["endpoint"]
    assert template.conditionals == {}


def test_conditional_flag_simple():
    template = PathTemplate.from_string("/{endpoint}/[all]")
    # Flag is False - should omit the conditional part
    assert template.format(endpoint="users", all=False) == "/users"
    # Flag is True - should include the flag name
    assert template.format(endpoint="users", all=True) == "/users/all"
    assert template.parameters == ["endpoint"]
    assert template.conditionals == {"all": ""}


def test_conditional_with_content():
    template = PathTemplate.from_string("/{endpoint}/[event:events]")
    # Flag is False - should omit the conditional part
    assert template.format(endpoint="users", event=False) == "/users"
    # Flag is True - should include the specified content
    assert template.format(endpoint="users", event=True) == "/users/events"
    assert template.parameters == ["endpoint"]
    assert template.conditionals == {"event": "events"}


def test_multiple_conditionals():
    template = PathTemplate.from_string("/{endpoint}/[all]/[event:events]")
    # Test all combinations
    assert template.format(endpoint="users", all=False, event=False) == "/users"
    assert template.format(endpoint="users", all=True, event=False) == "/users/all"
    assert template.format(endpoint="users", all=False, event=True) == "/users/events"
    assert template.format(endpoint="users", all=True, event=True) == "/users/all/events"
    assert template.parameters == ["endpoint"]
    assert template.conditionals == {"all": "", "event": "events"}


def test_multiple_parameters():
    template = PathTemplate.from_string("/{version}/{endpoint}/[all]")
    assert template.format(version="v1", endpoint="users", all=True) == "/v1/users/all"
    assert template.parameters == ["version", "endpoint"]
    assert template.conditionals == {"all": ""}


def test_equality():
    template1 = PathTemplate.from_string("/{endpoint}/[all]")
    template2 = PathTemplate.from_string("/{endpoint}/[all]")
    template3 = PathTemplate.from_string("/{endpoint}/[event:events]")

    assert template1 == template2
    assert template1 != template3
    assert template1 == "/{endpoint}/[all]"
    assert template1 != "different"


def test_contains():
    template = PathTemplate.from_string("/{version}/{endpoint}/[all]/[event:events]")
    assert "version" in template
    assert "endpoint" in template
    assert "all" in template
    assert "event" in template
    assert "nonexistent" not in template


def test_missing_required_parameter():
    template = PathTemplate.from_string("/{endpoint}/[all]")
    with pytest.raises(KeyError):
        template.format(all=True)  # Missing required 'endpoint' parameter


def test_extra_parameters():
    template = PathTemplate.from_string("/{endpoint}")
    # Extra parameters should be ignored
    assert template.format(endpoint="users", extra="ignored") == "/users"


def test_falsy_values():
    template = PathTemplate.from_string("/{endpoint}/[flag1]/[flag2:custom]")
    # Test with various falsy values
    assert template.format(endpoint="users", flag1=None, flag2=None) == "/users"
    assert template.format(endpoint="users", flag1=0, flag2=0) == "/users"
    assert template.format(endpoint="users", flag1="", flag2="") == "/users"
    assert template.format(endpoint="users", flag1=[], flag2=[]) == "/users"


def test_truthy_values():
    template = PathTemplate.from_string("/{endpoint}/[flag1]/[flag2:custom]")
    # Test with various truthy values
    assert template.format(endpoint="users", flag1=1, flag2=1) == "/users/flag1/custom"
    assert template.format(endpoint="users", flag1="yes", flag2="yes") == "/users/flag1/custom"
    assert template.format(endpoint="users", flag1=[1], flag2=[1]) == "/users/flag1/custom"


def test_empty_template():
    template = PathTemplate.from_string("")
    assert template.format() == ""
    assert template.parameters == []
    assert template.conditionals == {}
