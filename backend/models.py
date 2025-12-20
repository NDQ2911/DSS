from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import relationship

from .database import Base
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    gender = Column(String(16), nullable=False)
    major = Column(String(64), nullable=True)
    birthday = Column(Date, nullable=True)
    year = Column(Integer, nullable=True)
    introversion_score = Column(Integer, nullable=False, default=3)
    sleep_schedule_score = Column(Integer, nullable=False, default=3)
    cleanliness_score = Column(Integer, nullable=False, default=3)
    noise_tolerance = Column(Integer, nullable=False, default=3)
    smoking = Column(Boolean, nullable=False, default=False)
    additional_attributes = Column(JSON, nullable=False, default=dict)

    assignments = relationship("Assignment", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"Student(id={self.id}, name={self.name})"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    building = Column(String(64), nullable=False)
    room_code = Column(String(16), nullable=False, unique=True)
    floor = Column(Integer, nullable=False, default=1)
    capacity = Column(Integer, nullable=False)
    gender_restriction = Column(String(16), nullable=True)
    room_type = Column(String(16), nullable=False, default="double")
    noise_level = Column(Float, nullable=False, default=0.5)
    facilities = Column(JSON, nullable=False, default=list)
    current_occupancy = Column(Integer, nullable=False, default=0)

    assignments = relationship("Assignment", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Room(id={self.id}, capacity={self.capacity})"


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("student_id", name="uq_assignment_student"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    student = relationship("Student", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Assignment(room_id={self.room_id}, student_id={self.student_id})"


class LabeledData(Base):
    """Stores user feedback about student compatibility for weight learning.
    
    Users provide distance/compatibility scores between pairs of students.
    This data is used to train a Linear Regression model to learn optimal weights.
    """
    __tablename__ = "labeled_data"

    id = Column(Integer, primary_key=True, index=True)
    student1_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    student2_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    distance_score = Column(Float, nullable=False)  # User-provided distance (0-100)
    created_at = Column(Date, nullable=False)
    meta_info = Column(JSON, nullable=False, default=dict)  # Additional info

    def __repr__(self) -> str:  # pragma: no cover
        return f"LabeledData(student1={self.student1_id}, student2={self.student2_id}, score={self.distance_score})"