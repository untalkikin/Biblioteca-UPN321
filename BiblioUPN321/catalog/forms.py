from django import forms   
from .models import BibliographicRecord, Item, Person, Subject

class BibliographicRecordForm(forms.ModelForm):
    authors = forms.forms.CharField(
        required=False,
        help_text="Separados por ';' (Apellido, Nombre; Apellido, Nombre )"
    )
    subjects_input = forms.CharField(required=False, help_text="Materias separadas por ';'")
    
    class Meta:
        model = BibliographicRecord
        fields = [
            "title","subtitle","resource_type","edition","language","publish_year",
            "publisher","publish_place","isbn","issn","lccn","call_number",
            "physical_desc","series","notes","cover",
        ]
        
    def save(self, commit=True):
        instance = super().save(commit)
        #Autores
        authors_text = self.cleaned_data.get("authors", "")
        if commit:
            if authors_text:
                name = [x.strip() for x in authors_text.split(";") if x.strip()]
                for n in names:
                    p, _ = Person.objects.get_or_create(full_name=n)
                    instance.contributors.get_or_create(person=p)
                    
            #Materias
            subject_text = self.cleaned_data.get("subjects_input","")
            if subjects_text:
                terms = [x.strip() for x in subjects_text.split(";") if x.strip()]
                for t in terms:
                    s, _ = Subject.objects.get_or_create(term=t)
                    instance.subjects.add(s)
        return instance        