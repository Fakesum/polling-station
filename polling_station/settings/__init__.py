import typing

T = typing.TypeVar("T")
class Settings(dict):
    def __init__(self, dictionary, valid):
        super().__init__(self._validate(dictionary, valid))

    def _validate(self, given, valid, _root = True) -> dict[str, typing.Any]:
        for key in valid.keys():
            if not (key in given):
                if ("optional" in valid[key]) and (valid[key]["optional"] == True):
                    if "default" in valid[key]:
                        given[key] = valid[key]["default"]
                    continue
                else:
                    if ("optional" in valid[key]):
                        raise SyntaxError(f"non-optional setting: {key} missing.")

            if not ("optional" in valid[key]):
                given[key] = self._validate((given[key] if (key in given) else {}), valid[key], False)
                continue
            
            if not (isinstance(given[key], valid[key]["type"])):
                raise SyntaxError(f"""setting {key} is of type {type(key)}, but it should be of type: {valid[key]["type"]}""")
            
            if isinstance(given[key], int) or isinstance(given[key], float):
                if ("nmin" in valid[key]) and (given[key] < valid[key]["nmin"]):
                    raise SyntaxError(f"""setting {key} is less than {valid[key]["nmin"]}""")
                if ("nmax" in valid[key]) and (given[key] > valid[key]["nmax"]):
                    raise SyntaxError(f"""setting {key} is greater than {valid[key]["nmax"]}""")           
            
            if ("choices" in valid[key]) and (given[key] not in valid[key]["choices"]):
                raise SyntaxError(f"""Unknown {key} given: {given[key]}, valid choices are: {valid[key]["choices"]}""")
        return given