from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.reference import Reference

from app.exceptions.service_exceptions import InvalidResourceException
from app.models.bsn import BSN


class CarePlanExtractor:
    def __init__(self, careplan: CarePlan) -> None:
        self.careplan = careplan

    def get_subject_bsn(self) -> BSN:
        if self.careplan.subject is None:
            raise InvalidResourceException("Field 'subject' is missing in the request")

        if not isinstance(self.careplan.subject, Reference):
            raise InvalidResourceException("Field 'subject' is not a Reference")

        if self.careplan.subject.type is None:
            raise InvalidResourceException("Field 'subject.type' is missing in the request")

        if self.careplan.subject.type != "Patient":
            raise InvalidResourceException("Field 'subject' is not a Patient")

        if self.careplan.subject.identifier is None:
            raise InvalidResourceException("Field 'subject.identifier' is missing in the request")

        if not isinstance(self.careplan.subject.identifier, Identifier):
            raise InvalidResourceException("Field 'subject.identifier' is not an Identifier")

        if self.careplan.subject.identifier.system is None:
            raise InvalidResourceException("Field 'subject.identifier.system' is missing in the request")

        if self.careplan.subject.identifier.system != "http://fhir.nl/fhir/NamingSystem/bsn":
            raise InvalidResourceException("Field 'subject.identifier.system' is not 'http://fhir.nl/NamingSystem/bsn'")

        if self.careplan.subject.identifier.value is None:
            raise InvalidResourceException("Field 'subject.identifier.value' is missing in the request")

        return BSN(self.careplan.subject.identifier.value)
