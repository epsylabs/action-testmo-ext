from xml.etree.ElementTree import Element


def get_properties(properties: Element) -> dict:
    if properties is None:
        return {}

    return {p.get("name"): p.get("value") for p in properties.findall("property")}
