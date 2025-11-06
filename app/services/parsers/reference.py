import logging
from typing import Tuple

from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bodystructure import BodyStructure
from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.careteam import CareTeam
from fhir.resources.R4B.clinicalimpression import ClinicalImpression
from fhir.resources.R4B.detectedissue import DetectedIssue
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.familymemberhistory import FamilyMemberHistory
from fhir.resources.R4B.imagingstudy import ImagingStudy
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.immunizationevaluation import ImmunizationEvaluation
from fhir.resources.R4B.immunizationrecommendation import ImmunizationRecommendation
from fhir.resources.R4B.measurereport import MeasureReport
from fhir.resources.R4B.medicationadministration import MedicationAdministration
from fhir.resources.R4B.medicationdispense import MedicationDispense
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.medicationstatement import MedicationStatement
from fhir.resources.R4B.molecularsequence import MolecularSequence
from fhir.resources.R4B.nutritionorder import NutritionOrder
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.procedure import Procedure
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.riskassessment import RiskAssessment

logger = logging.getLogger(__name__)


class ReferenceParser:
    @staticmethod
    def get_patient_reference(resource: DomainResource) -> Reference | None:
        match resource:
            case AllergyIntolerance():
                return resource.patient

            case BodyStructure():
                return resource.patient

            case ImagingStudy():
                return resource.subject

            case CarePlan():
                return resource.subject

            case CareTeam():
                return resource.subject

            case ClinicalImpression():
                return resource.subject

            case Encounter():
                return resource.subject

            case DetectedIssue():
                return resource.patient

            case DiagnosticReport():
                return resource.subject

            case FamilyMemberHistory():
                return resource.patient

            case MedicationStatement():
                return resource.subject

            case MedicationAdministration():
                return resource.subject

            case MedicationDispense():
                return resource.subject

            case MedicationRequest():
                return resource.subject

            case Immunization():
                return resource.patient

            case ImmunizationEvaluation():
                return resource.patient

            case ImmunizationRecommendation():
                return resource.patient

            case MeasureReport():
                return resource.subject

            case MolecularSequence():
                return resource.patient

            case NutritionOrder():
                return resource.patient

            case Observation():
                return resource.subject

            case Procedure():
                return resource.subject

            case RiskAssessment():
                return resource.subject

            case _:
                return None

    @staticmethod
    def get_reference_type_and_id(
        reference: Reference,
    ) -> Tuple[str, str] | Tuple[None, None]:
        if reference.reference:
            try:
                split_data = reference.reference.split("/")
                return split_data[0], split_data[1]
            except IndexError as e:
                logger.warning(f"failed to retrieve resource type and id: {e}")
                return None, None

        return None, None
