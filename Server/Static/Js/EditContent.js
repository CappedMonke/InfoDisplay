document.addEventListener('DOMContentLoaded', function() {
    // Hide all forms
    document.querySelectorAll('.forms-content-page form').forEach(form => {
        form.style.display = 'none';
    });


    // Convert PascalCase to camelCase
    const toCamelCase = str => str.charAt(0).toLowerCase() + str.slice(1);


    // Show the form corresponding to content.type
    const formToShow = document.getElementById(`${toCamelCase(content.type)}Form`);
    if (formToShow) {
        formToShow.style.display = 'block';
        formToShow.setAttribute('action', '/update_content');
    }


    document.getElementById('saveButton').addEventListener('click', function() {
        const formData = new FormData(formToShow);
        
        let contentDict = {};
        formData.forEach((value, key) => {
            if (key !== 'duration' && key !== 'title') {
                contentDict[key] = value;
            }
        });

        const data = {
            id: content.id,
            title: formData.get('title'),
            duration: formData.get('duration'),
            content: contentDict,
        };

        fetch('/update_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })

        const updatedToast = document.getElementById('updatedToast')
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(updatedToast)
        toastBootstrap.show()
    });
});