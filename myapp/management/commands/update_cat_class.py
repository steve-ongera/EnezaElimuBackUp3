from django.core.management.base import BaseCommand
from myapp.models import CAT, Student, Class_of_study

class Command(BaseCommand):
    help = 'Update CAT records where class_of_study is NULL for multiple specific students'

    def handle(self, *args, **kwargs):
        # List of admission numbers to update (Add as many as you want here!)
        adm_numbers = ['ADM010', 'ADM017', 'ADM019', 'ADM023' , 'ADM028' , 'ADM031' , 'ADM034' , 'ADM038' , 'ADM043' , 'ADM052' ,'ADM071', 'ADM072', 'ADM074' , 'ADM075' , 'ADM076' , 'ADM084' ,'ADM092']

        try:
            # 1. Get the Class_of_study (Form 1 B)
            target_class = Class_of_study.objects.get(name='Form 3', stream='A')
            self.stdout.write(self.style.SUCCESS(f"Target Class found: {target_class}"))

            total_updated = 0

            for adm in adm_numbers:
                try:
                    # 2. Get the student
                    student = Student.objects.get(admission_number=adm)
                    self.stdout.write(self.style.SUCCESS(f"Student found: {student.name}"))

                    # 3. Filter CAT records where class_of_study is NULL
                    cat_records = CAT.objects.filter(student=student, class_of_study__isnull=True)
                    count = cat_records.count()

                    if count == 0:
                        self.stdout.write(self.style.WARNING(f"No CAT records found for {adm}."))
                    else:
                        # 4. Update all such records
                        cat_records.update(class_of_study=target_class)
                        self.stdout.write(self.style.SUCCESS(f"Updated {count} CAT records for {adm}."))
                        total_updated += count

                except Student.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Student with admission number {adm} not found."))

            self.stdout.write(self.style.SUCCESS(f"\nTotal CAT records updated: {total_updated}"))

        except Class_of_study.DoesNotExist:
            self.stdout.write(self.style.ERROR("Class_of_study 'Form 1 B' not found."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
