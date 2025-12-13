from marshmallow import EXCLUDE, Schema, fields, validate


class StudentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    gender = fields.Str(required=True)
    major = fields.Str(allow_none=True)
    birthday = fields.Date(allow_none=True)
    year = fields.Int(allow_none=True, validate=validate.Range(min=1, max=4))
    introversion_score = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    sleep_schedule_score = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    cleanliness_score = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    noise_tolerance = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    smoking = fields.Bool(load_default=False)
    additional_attributes = fields.Dict(keys=fields.Str(), values=fields.Raw(), load_default=dict)


class RoomSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    building = fields.Str(required=True)
    room_code = fields.Str(required=True)
    floor = fields.Int(load_default=1, validate=validate.Range(min=0))
    capacity = fields.Int(required=True, validate=validate.Range(min=1))
    gender_restriction = fields.Str(allow_none=True)
    room_type = fields.Str(load_default="double")
    noise_level = fields.Float(load_default=0.5, validate=validate.Range(min=0.0, max=1.0))
    facilities = fields.List(fields.Str(), load_default=list)
    current_occupancy = fields.Int(load_default=0, validate=validate.Range(min=0))


class AssignmentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    student_id = fields.Int(required=True)
    room_id = fields.Int(required=True)


class OptimizeParamsSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    initial_temperature = fields.Float(load_default=1000.0, validate=validate.Range(min=0.0001))
    cooling_rate = fields.Float(load_default=0.95, validate=validate.Range(min=0.0, max=1.0))
    iterations = fields.Int(load_default=3000, validate=validate.Range(min=1))


class StudentGenerationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    count = fields.Int(load_default=500, validate=validate.Range(min=1, max=5000))
    male_ratio = fields.Float(load_default=0.5, validate=validate.Range(min=0.0, max=1.0))
    smoking_ratio = fields.Float(load_default=0.15, validate=validate.Range(min=0.0, max=1.0))
    clear_existing = fields.Bool(load_default=True)


class RoomGenerationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    target_students = fields.Int(allow_none=True, validate=validate.Range(min=1))
    blocks = fields.Int(load_default=6, validate=validate.Range(min=1, max=20))
    floors_per_block = fields.Int(load_default=6, validate=validate.Range(min=1, max=15))
    rooms_per_floor = fields.Int(load_default=12, validate=validate.Range(min=1, max=20))
    capacity_choices = fields.List(
        fields.Int(validate=validate.OneOf([6, 8, 10])),
        load_default=[6, 8, 10],
    )
    clear_existing = fields.Bool(load_default=True)
    gender_strategy = fields.Str(
        load_default="alternating",
        validate=validate.OneOf(["alternating", "mixed"]),
    )
