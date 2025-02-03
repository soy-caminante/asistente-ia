async function searchPatient() 
{
    const query             = document.getElementById("searchInput").value;
    const response          = await fetch(`/api/patients/search?pattern=${query}`);
    const data              = await response.json();

    const resultsDiv        = document.getElementById("results");
    resultsDiv.innerHTML    = ''; // Limpiar resultados previos

    data.results.forEach(patient => {
        const div       = document.createElement("div");
        div.className   = "result-item";

        div.innerHTML = `
            <button onclick="loadPatientDetails('${patient.dni}')">Seleccionar</button>
            <p><strong>${patient.dni}</strong> - ${patient.apellidos}, ${patient.nombre}</p>
        `;

        resultsDiv.appendChild(div);
    });
}
//-------------------------------------------------------------------------------------------------

function fillListContent(element_id, data_list) 
{
    const targetList        = document.getElementById(element_id);
    targetList.innerHTML    = '';

    if (!Array.isArray(data_list)) 
    {
        throw new Error(`Error: ${element_id} - data_list no es un array válido. Es de tipo * ${data_list} *  ${typeof data_list}`);
    }
    
    if (data_list.length == 0) { return; }
    
    data_list.sort();
    data_list.forEach(data => {
        const listItem          = document.createElement("li");
        listItem.textContent    = data;
        targetList.appendChild(listItem);
    });
}
//-------------------------------------------------------------------------------------------------

function loadPatientDetails(patientId) 
{
    window.location.href = `/patient/${patientId}`;
}
//-------------------------------------------------------------------------------------------------

function getPatientId()
{
    const path      = window.location.pathname;
    const segments  = path.split('/');
    const patientId = segments[segments.length - 1];

    if (!patientId) 
    {
        throw new Error("No se ha proporcionado un ID de paciente válido.");
    }

    return patientId
}
//-------------------------------------------------------------------------------------------------

async function loadPatientData() 
{
    if (typeof marked !== "undefined") {
        console.log("Marked está disponible");
        const html = marked("# Hola Mundo!");
        console.log(html);
      } else {
        console.error("Marked no está disponible");
      }

    try
    {
        const patientId = getPatientId()
        const response  = await fetch(`/api/patients/patient_data?ref_id=${patientId}`);

        if (!response.ok) 
        {
            throw new Error("Error al cargar los datos del paciente.");
        }

        const data      = await response.json();

        document.getElementById("patientSurname").textContent       = `Apellidos: ${data.apellidos}`;
        document.getElementById("patientName").textContent          = `Nombre: ${data.nombre}`;
        document.getElementById("patientId").textContent            = `DNI: ${data.dni}`;
        document.getElementById("patientAge").textContent           = `Edad: ${data.edad}`;
        document.getElementById("patientSex").textContent           = `Sexo: ${data.sexo}`;

        console.log("Data recibido:", data);
        console.log("Medicacion recibido:", data.medicacion);

        fillListContent("patientRiskFactors",   data.riesgo);
        fillListContent("patientMedication",    data.medicacion);
        fillListContent("patientAllergies",     data.alergias);
        fillListContent("patientHistory",       data.antecedentes);
        fillListContent("patientVisits",        data.visitas);
        fillListContent("patientAdmissions",    data.ingresos);
    } 
    catch (error) 
    {
        console.error(error);
        alert(error);
    }
}
//-------------------------------------------------------------------------------------------------

// Función para manejar el chat
async function askChat() 
{
    try
    {
        const ref_id    = getPatientId()
        const question  = document.getElementById("chatInput").value.trim();
        
        if (!question) 
        {
            alert("Debes introducir una pregunta.");
            return;
        }

        const response = await fetch(`/api/chat/`, 
        {
            method:     "POST",
            headers:    { "Content-Type": "application/json" },
            body:       JSON.stringify({ ref_id, question })
        });

        const data              = await response.json();
        const chatBox           = document.getElementById("chatResponses");
        const responseDiv       = document.createElement("div");
        responseDiv.className   = "chat-response";

        const questionDiv       = document.createElement("div");
        questionDiv.className   = "question";
        questionDiv.textContent = question;

        const answerDiv         = document.createElement("div");
        answerDiv.className     = "answer";
        const response_info     = data.response.replace(/````markdown\n([\s\S]*?)````/g, "$1");
        const generationTime    = "<em><small>" + data.generation + "</small></em>"
        const markdownHTML      = marked(response_info + "\r\n" + generationTime);
        answerDiv.innerHTML     = markdownHTML;

        responseDiv.appendChild(questionDiv);
        responseDiv.appendChild(answerDiv);
        chatBox.appendChild(responseDiv);

        document.getElementById("chatInput").value = '';
    }
    catch (error) 
    {
        console.error(error);
        alert(error);
    }
}
//-------------------------------------------------------------------------------------------------

// Función para volver a la pantalla inicial
function goToHome() 
{
    window.location.href = "/";
}
//-------------------------------------------------------------------------------------------------
