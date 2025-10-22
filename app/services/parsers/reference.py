from typing import Tuple

from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.imagingstudy import ImagingStudy
from fhir.resources.R4B.reference import Reference


class ReferenceParser:
    @staticmethod
    def get_patient_reference(resource: DomainResource) -> Reference | None:
        if isinstance(resource, ImagingStudy):
            return resource.subject

        if isinstance(resource, CarePlan):
            return resource.subject

        return None

    @staticmethod
    def get_reference_type_and_id(
        reference: Reference,
    ) -> Tuple[str, str] | Tuple[None, None]:
        if reference.reference:
            split_data = reference.reference.split("/")
            return split_data[0], split_data[1]

        return None, None
