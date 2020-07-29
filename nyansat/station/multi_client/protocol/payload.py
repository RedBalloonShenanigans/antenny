class MultiAntennyPayload(object):

    def __init__(
            self,
            payload_type: int
    ):
        self.payload_type = payload_type

    def serialize(self):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, payload: bytes):
        raise NotImplementedError
