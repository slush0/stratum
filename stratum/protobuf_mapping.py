import stratum_pb2 as proto

map_type_to_class = {}
map_class_to_type = {}

map_class_to_json = {}
map_json_to_class = {}

def build_map():
    for msg_type, i in proto.MessageType.items():
        msg_name = msg_type.replace('MessageType_', '')
        msg_class = getattr(proto, msg_name)

        map_type_to_class[i] = msg_class
        map_class_to_type[msg_class] = i

        json_method = proto.MessageType.DESCRIPTOR.values_by_number[i].GetOptions().Extensions[proto.json]

        map_class_to_json[msg_class] = json_method
        map_json_to_class[json_method] = msg_class

def get_type(msg):
    return map_class_to_type[msg.__class__]

def get_class(t):
    return map_type_to_class[t]

def get_class_by_json(j):
    return map_json_to_class[j]

def get_json_by_class(msg):
    return map_class_to_json[msg.__class__]

def check_missing():
    from google.protobuf import reflection

    types = [getattr(proto, item) for item in dir(proto)
             if issubclass(getattr(proto, item).__class__, reflection.GeneratedProtocolMessageType)]

    missing = list(set(types) - set(map_type_to_class.values()))

    if len(missing):
        raise Exception("Following protobuf messages are not defined in mapping: %s" % missing)

build_map()
check_missing()
