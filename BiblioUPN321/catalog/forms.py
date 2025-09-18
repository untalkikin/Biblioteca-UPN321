from django import forms   
from .models import BibliographicRecord, Item, Person, Subject


class BibliographicRecordForm(forms.ModelForm):
    """Formulario para crear/editar registros bibliográficos.

    Campos auxiliares:
    - `authors`: texto con autores separados por `;` que se convertirá en
      relaciones `RecordContributor` con rol por defecto 'author'.
    - `subjects_input`: texto con materias separadas por `;` que se
      convertirán en instancias de `Subject` si no existen.
    """
    authors = forms.CharField(
        required=False,
        help_text="Separados por ';' (Apellido, Nombre; Apellido, Nombre )"
    )
    subjects_input = forms.CharField(required=False, help_text="Materias separadas por ';'")
    
    class Meta:
        model = BibliographicRecord
        fields = "__all__"
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),  # si es choices
            'edition': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.TextInput(attrs={'class': 'form-control'}),
            'publish_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-select'}),      # si es FK
            'publish_place': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'issn': forms.TextInput(attrs={'class': 'form-control'}),
            'iccn': forms.TextInput(attrs={'class': 'form-control'}),
            'call_number': forms.TextInput(attrs={'class': 'form-control'}),
            'physical_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'series': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

        
    def save(self, commit=True):
        """Guarda el registro y crea/actualiza autores y materias opcionales.

        - Si `commit` es True se guardan las relaciones de autores y materias.
        - Convierte cada autor en una `Person` (si no existe) y crea la
          relación con el registro.
        - Convierte cada término de `subjects_input` en `Subject`.
        """
        instance = super().save(commit)

        # Manejo de autores (campo libre transformado en relaciones)
        authors_text = self.cleaned_data.get("authors", "")
        if commit:
            if authors_text:
                names = [x.strip() for x in authors_text.split(";") if x.strip()]
                for n in names:
                    p, _ = Person.objects.get_or_create(full_name=n)
                    # Use related_name 'contributors' en RecordContributor
                    instance.contributors.get_or_create(person=p)
                    
            # Manejo de materias (Subjects)
            subjects_text = self.cleaned_data.get("subjects_input", "")
            if subjects_text:
                terms = [x.strip() for x in subjects_text.split(";") if x.strip()]
                for t in terms:
                    s, _ = Subject.objects.get_or_create(term=t)
                    instance.subjects.add(s)
        return instance