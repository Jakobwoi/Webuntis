function getInfo(element) {
            
        }
async function parseTimeTable() {
    let weekdays = ['mo', 'tu', 'we', 'th', 'fr'];
    let data = await fetch('timetable2.json')
    data = await data.text();
    let json = JSON.parse(data);
    document.getElementById('info').innerText = json["tu"][4]["room"];
    for (let day of weekdays) {
        for (let lessonNumber = 1; lessonNumber <= 11; lessonNumber++) {
            let lessonKey = json[day][lessonNumber];
            let buttonId = day + '-' + lessonNumber;
            let buttonElement = document.getElementById(buttonId);
            if (lessonKey["teacherShort"] !== undefined) {
                buttonElement.innerHTML = `
                <div>
                    <span class="teacher-name">${lessonKey["class"]}</span><br>
                    <span class="subject">${lessonKey["subject"]}</span><br>
                    <span class="room">${lessonKey["room"]}</span>
                </div>`;
            }
            else {
                buttonElement.innerHTML = '';
                buttonElement.disabled = true;
                buttonElement.style.visibility = 'hidden';
            }
        }
    }
}